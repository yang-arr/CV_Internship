#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
重建API路由
包含图像重建相关的接口
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
import aiofiles
import os
import uuid
import numpy as np
from datetime import datetime
from tempfile import NamedTemporaryFile
from sqlalchemy.orm import Session
import base64
from PIL import Image
import io

from MRI.app.services.db import get_db
from MRI.app.services.auth import get_current_user
from MRI.app.models.user import User
from MRI.app.services.model_service import model_service

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 获取可用模型列表
@router.get("/models")
async def get_available_models(current_user: User = Depends(get_current_user)):
    """获取可用的重建模型列表"""
    try:
        logger.info("获取可用模型列表")
        models = model_service.get_models_list()
        
        # 转换为API响应格式
        models_list = []
        for model in models:
            models_list.append({
                "id": model.get("id", ""),
                "name": model.get("name", ""),
                "description": model.get("description", ""),
                "created_at": model.get("created_at", datetime.now().isoformat())
            })
        
        logger.info(f"找到 {len(models_list)} 个可用模型")
        return {"models": models_list}
    except Exception as e:
        logger.error(f"获取模型列表时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

# 提交重建任务
@router.post("/")
async def reconstruct_image(
    file: UploadFile = File(...),
    model_id: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """提交图像重建任务"""
    try:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="仅支持图像文件")
        
        logger.info(f"开始重建图像，使用模型: {model_id}")
        
        # 读取上传的图像文件
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # 转换为灰度图并调整大小
        if image.mode != 'L':
            image = image.convert('L')
        
        # 调整图像大小为256x256（或其他模型需要的尺寸）
        image = image.resize((256, 256))
        
        # 转换为NumPy数组
        input_data = np.array(image)
        
        # 使用模型进行预测
        start_time = datetime.now()
        result = model_service.predict(model_id, input_data)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # 将重建结果转换为base64编码的图像
        reconstructed_image = result["reconstructed_image"]
        img = Image.fromarray((reconstructed_image * 255).astype(np.uint8))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # 获取评估指标
        metrics = result["metrics"]
        
        return {
            "success": True,
            "message": "图像重建成功",
            "result_id": str(uuid.uuid4()),
            "reconstructed_image": img_str,
            "metrics": metrics,
            "execution_time": execution_time
        }
    except Exception as e:
        logger.error(f"重建图像时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"重建失败: {str(e)}")

# 获取重建结果
@router.get("/results/{result_id}")
async def get_reconstruction_result(
    result_id: str, 
    current_user: User = Depends(get_current_user)
):
    """获取重建结果"""
    try:
        # 模拟获取重建结果
        return {
            "result_id": result_id,
            "status": "completed",
            "reconstructed_image": "base64_encoded_image_data_here",
            "metrics": {
                "psnr": 30.5,
                "ssim": 0.9123,
                "nse": 0.0542
            },
            "execution_time": 2.35
        }
    except Exception as e:
        logger.error(f"获取重建结果时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取结果失败: {str(e)}")

# 获取任务状态
@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str, 
    current_user: User = Depends(get_current_user)
):
    """获取任务状态"""
    try:
        # 模拟获取任务状态
        return {
            "task_id": task_id,
            "status": "completed",
            "progress": 100,
            "message": "重建已完成"
        }
    except Exception as e:
        logger.error(f"获取任务状态时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}") 