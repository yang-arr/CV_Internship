from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import aiohttp
import json
import logging
import tempfile
import os
import io
from typing import Optional
import uuid
import speech_recognition as sr
from gtts import gTTS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class Question(BaseModel):
    text: str

class Answer(BaseModel):
    response: str

class TTSRequest(BaseModel):
    text: str
    lang: str = "zh"
    slow: bool = False

OLLAMA_API_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "hf.co/TimeLoad/deepseek-r1-medical:latest"
MODEL_NAME = "deepseek-r1:7b"

@router.post("/ask")
async def ask_medical_question(question: Question):
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
                    
                    return JSONResponse(
                        status_code=200,
                        content={"response": result["response"]}
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