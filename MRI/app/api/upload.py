#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件上传API路由
处理文件上传相关的请求，如图像上传
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
import uuid
import time
import shutil
from pathlib import Path
import numpy as np
from PIL import Image
import io

from MRI.app.services.auth import get_current_user
from MRI.app.models.user import User

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 上传目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = str(BASE_DIR / "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 数据模型
class UploadResponse(BaseModel):
    """上传响应模型"""
    file_id: str
    filename: str
    content_type: str
    size: int
    uploaded_at: float

@router.post("/", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    上传文件，支持图像文件
    
    Args:
        file: 上传的文件
        
    Returns:
        UploadResponse: 上传成功的响应
    """
    logger.info(f"Received file upload: {file.filename}")
    
    try:
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        
        # 创建上传目录（如果不存在）
        file_dir = os.path.join(UPLOAD_DIR, file_id)
        os.makedirs(file_dir, exist_ok=True)
        
        # 构建文件路径
        file_path = os.path.join(file_dir, file.filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 生成响应
        response = UploadResponse(
            file_id=file_id,
            filename=file.filename,
            content_type=file.content_type,
            size=file_size,
            uploaded_at=time.time()
        )
        
        logger.info(f"File uploaded successfully: {file_id}")
        return response
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/images/", response_model=Dict[str, Any])
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: str = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    上传MRI图像
    
    参数:
    - file: 要上传的图像文件
    - description: 图像描述（可选）
    
    返回:
    - 图像信息和保存路径
    """
    logger.info(f"Received image upload: {file.filename}")
    
    try:
        # 检查文件类型
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="只接受图像文件")
        
        # 读取文件内容
        content = await file.read()
        
        # 检查是否为有效图像
        try:
            Image.open(io.BytesIO(content))
        except Exception:
            raise HTTPException(status_code=400, detail="无效的图像文件")
        
        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 返回结果
        return {
            "filename": filename,
            "original_filename": file.filename,
            "content_type": file.content_type,
            "file_size": len(content),
            "file_path": file_path,
            "description": description,
            "user_id": current_user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传图像时出错: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.get("/{file_id}")
async def get_file_info(file_id: str):
    """
    获取已上传文件的信息
    
    Args:
        file_id: 文件ID
        
    Returns:
        Dict: 文件信息
    """
    file_dir = os.path.join(UPLOAD_DIR, file_id)
    
    if not os.path.exists(file_dir):
        raise HTTPException(status_code=404, detail=f"File with ID '{file_id}' not found")
    
    try:
        # 获取目录中的文件
        files = os.listdir(file_dir)
        if not files:
            raise HTTPException(status_code=404, detail=f"No files found for ID '{file_id}'")
        
        # 排除缩略图
        main_files = [f for f in files if not f.startswith("thumbnail_")]
        if not main_files:
            raise HTTPException(status_code=404, detail=f"Main file not found for ID '{file_id}'")
        
        # 获取主文件
        main_file = main_files[0]
        file_path = os.path.join(file_dir, main_file)
        
        # 检查缩略图是否存在
        thumbnail_path = os.path.join(file_dir, f"thumbnail_{main_file}")
        thumbnail_available = os.path.exists(thumbnail_path)
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        modified_time = os.path.getmtime(file_path)
        
        # 尝试获取图像信息
        image_info = {}
        try:
            with Image.open(file_path) as img:
                image_info = {
                    "dimensions": {
                        "width": img.width,
                        "height": img.height
                    },
                    "format": img.format,
                    "mode": img.mode
                }
        except:
            # 不是图像文件或无法打开
            pass
        
        return {
            "file_id": file_id,
            "filename": main_file,
            "size": file_size,
            "modified_at": modified_time,
            "thumbnail_available": thumbnail_available,
            **image_info
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 