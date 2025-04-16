from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import aiohttp
import json
import logging
import tempfile
import os
import io
from typing import Optional, List
import uuid
import speech_recognition as sr
from gtts import gTTS
from sqlalchemy.orm import Session
from MRI.app.services.db import get_db
from MRI.app.models import ChatHistory, ChatMessage, User
from MRI.app.services.auth import get_current_user

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class Question(BaseModel):
    text: str
    chat_history_id: Optional[int] = None  # 可选的聊天历史ID

class Answer(BaseModel):
    response: str

class TTSRequest(BaseModel):
    text: str
    lang: str = "zh"
    slow: bool = False

class ChatHistoryCreate(BaseModel):
    title: str

class ChatHistoryResponse(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str
    message_count: int

class ChatMessageResponse(BaseModel):
    id: int
    content: str
    is_user: bool
    sequence: int
    created_at: str

class ChatHistoryDetailResponse(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: str
    messages: List[ChatMessageResponse]

OLLAMA_API_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "hf.co/TimeLoad/deepseek-r1-medical:latest"
MODEL_NAME = "deepseek-r1:7b"

@router.post("/ask")
async def ask_medical_question(question: Question, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    向医疗AI模型提问并获取回答
    
    Args:
        question: 用户提出的医疗相关问题
        
    Returns:
        JSONResponse: 包含AI回答或错误信息的JSON响应
    """
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": MODEL_NAME,
                "prompt": question.text,
                "stream": False
            }
            
            try:
                async with session.post(OLLAMA_API_URL, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Ollama服务响应错误: status={response.status}")
                        return JSONResponse(
                            status_code=500,
                            content={"error": "模型服务器响应错误", "details": f"状态码: {response.status}"}
                        )
                    
                    result = await response.json()
                    if not result or "response" not in result:
                        logger.error("Ollama服务返回无效响应")
                        return JSONResponse(
                            status_code=500,
                            content={"error": "无效的模型响应", "details": "响应格式不正确"}
                        )
                    
                    # 保存对话记录到数据库
                    ai_response = result["response"]
                    
                    # 处理历史记录
                    chat_history_id = question.chat_history_id
                    
                    # 如果没有提供会话ID，创建新会话
                    if not chat_history_id:
                        # 使用问题前20个字符作为标题
                        title = question.text[:20] + "..." if len(question.text) > 20 else question.text
                        chat_history = ChatHistory(
                            user_id=current_user.id,
                            title=title
                        )
                        db.add(chat_history)
                        db.flush()  # 刷新以获取ID
                        chat_history_id = chat_history.id
                    else:
                        # 检查会话是否存在且属于当前用户
                        chat_history = db.query(ChatHistory).filter(
                            ChatHistory.id == chat_history_id,
                            ChatHistory.user_id == current_user.id
                        ).first()
                        
                        if not chat_history:
                            return JSONResponse(
                                status_code=404,
                                content={"error": "会话记录不存在或无权访问"}
                            )
                    
                    # 获取当前会话的最大序号
                    max_sequence = db.query(ChatMessage).filter(
                        ChatMessage.chat_history_id == chat_history_id
                    ).count()
                    
                    # 保存用户问题
                    user_message = ChatMessage(
                        chat_history_id=chat_history_id,
                        content=question.text,
                        is_user=True,
                        sequence=max_sequence
                    )
                    db.add(user_message)
                    
                    # 保存AI回答
                    ai_message = ChatMessage(
                        chat_history_id=chat_history_id,
                        content=ai_response,
                        is_user=False,
                        sequence=max_sequence + 1
                    )
                    db.add(ai_message)
                    
                    db.commit()
                    
                    return JSONResponse(
                        status_code=200,
                        content={
                            "response": ai_response,
                            "chat_history_id": chat_history_id
                        }
                    )
                    
            except aiohttp.ClientError as e:
                logger.error(f"连接Ollama服务失败: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "无法连接到模型服务器", "details": str(e)}
                )
                
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "内部服务器错误", "details": str(e)}
        )

@router.post("/speech-to-text")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """
    语音转文本API
    
    Args:
        audio_file: 上传的音频文件(支持wav, mp3格式)
        
    Returns:
        JSONResponse: 包含识别的文本或错误信息
    """
    try:
        # 创建临时文件保存上传的音频
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.wav")
        
        # 保存上传的文件
        with open(temp_file_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        # 初始化语音识别
        recognizer = sr.Recognizer()
        
        # 从文件加载音频
        with sr.AudioFile(temp_file_path) as source:
            # 录制音频数据
            audio_data = recognizer.record(source)
            
            # 使用Google Web Speech API识别音频
            text = recognizer.recognize_google(audio_data, language="zh-CN")
            
            return JSONResponse(
                status_code=200,
                content={"text": text}
            )
            
    except sr.UnknownValueError:
        return JSONResponse(
            status_code=400,
            content={"error": "无法识别语音内容"}
        )
    except sr.RequestError as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"语音识别服务错误: {str(e)}"}
        )
    except Exception as e:
        logger.error(f"处理语音识别时出错: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "语音识别处理失败", "details": str(e)}
        )
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

@router.post("/text-to-speech")
async def text_to_speech(tts_request: TTSRequest):
    """
    文本转语音API
    
    Args:
        tts_request: 包含要转换为语音的文本和相关参数
        
    Returns:
        StreamingResponse: 音频文件流
    """
    try:
        # 使用gTTS将文本转换为语音
        tts = gTTS(text=tts_request.text, lang=tts_request.lang, slow=tts_request.slow)
        
        # 创建内存文件对象存储音频
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # 返回音频文件
        return StreamingResponse(
            fp, 
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
        
    except Exception as e:
        logger.error(f"文本转语音处理失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "文本转语音处理失败", "details": str(e)}
        )

# 聊天历史相关API

@router.get("/chat-history", response_model=List[ChatHistoryResponse])
async def get_chat_histories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取用户的所有聊天历史记录"""
    histories = db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id).order_by(ChatHistory.updated_at.desc()).all()
    
    result = []
    for history in histories:
        # 获取消息数量
        message_count = db.query(ChatMessage).filter(ChatMessage.chat_history_id == history.id).count()
        result.append({
            "id": history.id,
            "title": history.title,
            "created_at": history.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": history.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "message_count": message_count
        })
    
    return result

@router.get("/chat-history/{history_id}", response_model=ChatHistoryDetailResponse)
async def get_chat_history_detail(history_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取特定聊天历史的详细信息，包括所有消息"""
    history = db.query(ChatHistory).filter(
        ChatHistory.id == history_id,
        ChatHistory.user_id == current_user.id
    ).first()
    
    if not history:
        raise HTTPException(status_code=404, detail="会话记录不存在或无权访问")
    
    # 获取所有消息
    messages = db.query(ChatMessage).filter(
        ChatMessage.chat_history_id == history_id
    ).order_by(ChatMessage.sequence).all()
    
    return {
        "id": history.id,
        "title": history.title,
        "created_at": history.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": history.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        "messages": [
            {
                "id": msg.id,
                "content": msg.content,
                "is_user": msg.is_user,
                "sequence": msg.sequence,
                "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for msg in messages
        ]
    }

@router.delete("/chat-history/{history_id}")
async def delete_chat_history(history_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """删除指定的聊天历史记录"""
    history = db.query(ChatHistory).filter(
        ChatHistory.id == history_id,
        ChatHistory.user_id == current_user.id
    ).first()
    
    if not history:
        raise HTTPException(status_code=404, detail="会话记录不存在或无权访问")
    
    # 删除历史记录（关联的消息会通过级联删除）
    db.delete(history)
    db.commit()
    
    return {"message": "会话记录已成功删除"} 