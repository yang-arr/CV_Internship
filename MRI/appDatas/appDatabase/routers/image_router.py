from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import time
import os
import json
import uuid
from datetime import datetime
from PIL import Image as PILImage

from MRI.appDatas.appDatabase.schemas import ImageInfo, ImageUploadResponse, InferenceRequest, InferenceResponse, InferenceTaskResponse
from MRI.appDatas.appDatabase.database.db import User, Image, InferenceResult, get_db
from MRI.appDatas.appDatabase.utils.image_utils import ImageProcessor
from MRI.appDatas.appDatabase.utils.exceptions import ImageProcessingException, ModelInferenceException, ResourceNotFoundException
from MRI.appDatas.appDatabase.models.model_interface import create_model
from MRI.appDatas.appDatabase.routers.user_router import get_current_user

# 创建路由器
router = APIRouter(
    prefix="/images",
    tags=["图像"],
    responses={404: {"description": "未找到"}},
)

# 创建日志记录器
logger = logging.getLogger("image_router")

# 用于存储长时间运行任务的字典
inference_tasks = {}


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传图像文件
    
    - **file**: 要上传的图像文件（支持格式：JPG, JPEG, PNG, BMP, GIF）
    
    返回：
    - 上传成功的响应信息
    """
    # 检查文件类型
    allowed_types = ["image/jpeg", "image/png", "image/bmp", "image/gif"]
    if file.content_type not in allowed_types:
        raise ImageProcessingException(
            detail=f"不支持的文件类型: {file.content_type}，支持的类型: {', '.join(allowed_types)}"
        )
    
    try:
        # 读取文件内容
        contents = await file.read()
        file_size = len(contents)
        
        # 文件大小限制（10 MB）
        if file_size > 10 * 1024 * 1024:
            raise ImageProcessingException(
                detail="文件大小超过限制(10MB)"
            )
        
        # 验证图像数据
        is_valid, error_msg = ImageProcessor.validate_image(contents)
        if not is_valid:
            raise ImageProcessingException(
                detail=f"无效的图像数据: {error_msg}"
            )
        
        # 保存图像
        filename, filepath = ImageProcessor.save_image(contents)
        
        # 获取图像信息
        img = PILImage.open(filepath)
        width, height = img.size
        
        # 保存到数据库
        db_image = Image(
            user_id=current_user.id,
            filename=filename,
            original_path=filepath,
            file_size=file_size,
            mime_type=file.content_type,
            width=width,
            height=height
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        
        # 生成图像URL
        image_url = f"/static/uploads/{filename}"
        
        logger.info(f"图像上传成功: {filename}, 用户: {current_user.username}")
        
        return {
            "id": db_image.id,
            "filename": filename,
            "success": True,
            "message": "图像上传成功",
            "image_url": image_url
        }
    
    except ImageProcessingException as e:
        logger.error(f"图像处理错误: {str(e)}")
        raise
    
    except Exception as e:
        logger.error(f"上传图像时发生错误: {str(e)}")
        raise ImageProcessingException(
            detail=f"上传图像失败: {str(e)}"
        )
    
    finally:
        # 重置文件指针
        await file.seek(0)


@router.get("/", response_model=List[ImageInfo])
async def get_user_images(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    获取当前用户的所有图像
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数量上限
    
    返回：
    - 图像信息列表
    """
    images = db.query(Image).filter(
        Image.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return images


@router.get("/{image_id}", response_model=ImageInfo)
async def get_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定图像的信息
    
    - **image_id**: 图像ID
    
    返回：
    - 图像信息
    """
    image = db.query(Image).filter(
        Image.id == image_id,
        Image.user_id == current_user.id
    ).first()
    
    if not image:
        raise ResourceNotFoundException(
            detail=f"未找到ID为{image_id}的图像"
        )
    
    return image


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除指定图像
    
    - **image_id**: 图像ID
    
    返回：
    - 204 No Content
    """
    image = db.query(Image).filter(
        Image.id == image_id,
        Image.user_id == current_user.id
    ).first()
    
    if not image:
        raise ResourceNotFoundException(
            detail=f"未找到ID为{image_id}的图像"
        )
    
    # 删除物理文件（如果存在）
    try:
        if os.path.exists(image.original_path):
            os.remove(image.original_path)
        
        if image.processed_path and os.path.exists(image.processed_path):
            os.remove(image.processed_path)
    except Exception as e:
        logger.error(f"删除图像文件时发生错误: {str(e)}")
    
    # 删除相关的推理结果
    db.query(InferenceResult).filter(
        InferenceResult.image_id == image_id
    ).delete()
    
    # 删除图像记录
    db.delete(image)
    db.commit()
    
    logger.info(f"图像删除成功: {image_id}, 用户: {current_user.username}")
    
    return None


@router.post("/inference", response_model=InferenceResponse)
async def run_inference(
    inference_request: InferenceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    对图像进行模型推理（同步）
    
    - **inference_request**: 推理请求参数
    
    返回：
    - 推理结果
    """
    # 获取图像
    image = db.query(Image).filter(
        Image.id == inference_request.image_id,
        Image.user_id == current_user.id
    ).first()
    
    if not image:
        raise ResourceNotFoundException(
            detail=f"未找到ID为{inference_request.image_id}的图像"
        )
    
    try:
        # 加载图像
        img = ImageProcessor.load_image(image.original_path)
        if img is None:
            raise ImageProcessingException(
                detail=f"无法加载图像: {image.original_path}"
            )
        
        # 创建模型实例
        model = create_model(inference_request.model_name)
        
        # 执行推理
        start_time = time.time()
        result, processing_time = model.inference(img)
        
        # 创建推理结果记录
        top_predictions = result.get('top_predictions', [])
        top_predictions_json = json.dumps([
            {"class": pred["class"], "probability": pred["probability"]} 
            for pred in top_predictions
        ])
        
        inference_result = InferenceResult(
            image_id=image.id,
            model_name=inference_request.model_name,
            result_data=json.dumps(result),
            confidence=result.get('confidence', 0.0),
            processing_time=processing_time,
            status="completed"
        )
        db.add(inference_result)
        db.commit()
        db.refresh(inference_result)
        
        logger.info(f"推理完成: 图像={image.id}, 模型={inference_request.model_name}, 用户={current_user.username}")
        
        # 构造响应
        response = {
            "id": inference_result.id,
            "image_id": image.id,
            "model_name": inference_request.model_name,
            "top_class": result.get('top_class', ''),
            "confidence": result.get('confidence', 0.0),
            "top_predictions": [
                {"class_name": pred["class"], "probability": pred["probability"]} 
                for pred in top_predictions
            ],
            "processing_time": processing_time,
            "status": "completed",
            "created_at": inference_result.created_at
        }
        
        return response
        
    except ImageProcessingException as e:
        logger.error(f"图像处理错误: {str(e)}")
        raise
        
    except Exception as e:
        logger.error(f"推理过程中发生错误: {str(e)}")
        raise ModelInferenceException(
            detail=f"推理失败: {str(e)}"
        )


# 后台任务函数
async def run_inference_task(
    task_id: str,
    image_id: int,
    model_name: str,
    parameters: Optional[Dict[str, Any]],
    db: Session
):
    """
    在后台运行推理任务
    """
    try:
        # 更新任务状态
        inference_tasks[task_id]["status"] = "processing"
        
        # 获取图像
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            inference_tasks[task_id]["status"] = "failed"
            inference_tasks[task_id]["error"] = f"未找到ID为{image_id}的图像"
            return
        
        # 加载图像
        img = ImageProcessor.load_image(image.original_path)
        if img is None:
            inference_tasks[task_id]["status"] = "failed"
            inference_tasks[task_id]["error"] = f"无法加载图像: {image.original_path}"
            return
        
        # 创建模型实例
        model = create_model(model_name)
        
        # 执行推理
        result, processing_time = model.inference(img)
        
        # 创建推理结果记录
        top_predictions = result.get('top_predictions', [])
        
        inference_result = InferenceResult(
            image_id=image.id,
            model_name=model_name,
            result_data=json.dumps(result),
            confidence=result.get('confidence', 0.0),
            processing_time=processing_time,
            status="completed"
        )
        db.add(inference_result)
        db.commit()
        db.refresh(inference_result)
        
        # 更新任务状态
        inference_tasks[task_id]["status"] = "completed"
        inference_tasks[task_id]["result_id"] = inference_result.id
        inference_tasks[task_id]["result_url"] = f"/images/inference/{inference_result.id}"
        
        logger.info(f"后台推理任务完成: {task_id}, 图像={image.id}, 模型={model_name}")
        
    except Exception as e:
        logger.error(f"后台推理任务出错: {task_id}, {str(e)}")
        inference_tasks[task_id]["status"] = "failed"
        inference_tasks[task_id]["error"] = str(e)


@router.post("/inference/async", response_model=InferenceTaskResponse)
async def run_inference_async(
    inference_request: InferenceRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    对图像进行模型推理（异步）
    
    - **inference_request**: 推理请求参数
    
    返回：
    - 推理任务信息
    """
    # 获取图像
    image = db.query(Image).filter(
        Image.id == inference_request.image_id,
        Image.user_id == current_user.id
    ).first()
    
    if not image:
        raise ResourceNotFoundException(
            detail=f"未找到ID为{inference_request.image_id}的图像"
        )
    
    # 创建任务ID
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    inference_tasks[task_id] = {
        "image_id": image.id,
        "model_name": inference_request.model_name,
        "parameters": inference_request.parameters,
        "status": "pending",
        "created_at": datetime.now(),
        "user_id": current_user.id
    }
    
    # 添加后台任务
    background_tasks.add_task(
        run_inference_task,
        task_id,
        image.id,
        inference_request.model_name,
        inference_request.parameters,
        db
    )
    
    logger.info(f"异步推理任务已创建: {task_id}, 图像={image.id}, 模型={inference_request.model_name}, 用户={current_user.username}")
    
    # 返回任务信息
    return {
        "task_id": task_id,
        "status": "pending",
        "image_id": image.id,
        "created_at": inference_tasks[task_id]["created_at"],
        "result_url": f"/images/inference/tasks/{task_id}"
    }


@router.get("/inference/tasks/{task_id}", response_model=InferenceTaskResponse)
async def get_inference_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取推理任务的状态
    
    - **task_id**: 任务ID
    
    返回：
    - 推理任务信息
    """
    if task_id not in inference_tasks:
        raise ResourceNotFoundException(
            detail=f"未找到ID为{task_id}的推理任务"
        )
    
    task = inference_tasks[task_id]
    
    # 检查权限
    if task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="没有权限访问此任务"
        )
    
    response = {
        "task_id": task_id,
        "status": task["status"],
        "image_id": task["image_id"],
        "created_at": task["created_at"],
    }
    
    # 如果任务已完成，添加结果URL
    if task["status"] == "completed" and "result_url" in task:
        response["result_url"] = task["result_url"]
    
    return response


@router.get("/inference/{result_id}", response_model=InferenceResponse)
async def get_inference_result(
    result_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取推理结果
    
    - **result_id**: 结果ID
    
    返回：
    - 推理结果
    """
    # 获取推理结果
    result = db.query(InferenceResult).join(Image).filter(
        InferenceResult.id == result_id,
        Image.user_id == current_user.id
    ).first()
    
    if not result:
        raise ResourceNotFoundException(
            detail=f"未找到ID为{result_id}的推理结果"
        )
    
    # 解析结果数据
    result_data = json.loads(result.result_data)
    top_predictions = result_data.get('top_predictions', [])
    
    # 构造响应
    response = {
        "id": result.id,
        "image_id": result.image_id,
        "model_name": result.model_name,
        "top_class": result_data.get('top_class', ''),
        "confidence": result.confidence,
        "top_predictions": [
            {"class_name": pred["class"], "probability": pred["probability"]} 
            for pred in top_predictions
        ],
        "processing_time": result.processing_time,
        "status": result.status,
        "created_at": result.created_at
    }
    
    return response 