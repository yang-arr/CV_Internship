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
from MRI.app.models.reconstruction_history import ReconstructionHistory
from MRI.app.services.model_service import model_service

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 获取可用模型列表
@router.get("/models")
async def get_available_models():
    """获取可用的重建模型列表"""
    try:
        logger.info("获取可用模型列表")
        models = model_service.get_models_list()
        
        # 直接返回模型列表，无需额外处理
        logger.info(f"找到 {len(models)} 个可用模型")
        return {"models": models}
    except Exception as e:
        logger.error(f"获取模型列表时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

# 提交重建任务
@router.post("/")
async def reconstruct_image(
    file: UploadFile = File(...),
    model_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交图像重建任务"""
    try:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="仅支持图像文件")
        
        logger.info(f"开始重建图像，使用模型: {model_id}")
        
        # 读取上传的图像文件
        contents = await file.read()
        input_image = Image.open(io.BytesIO(contents))
        
        # 保存原始图像大小
        original_size = input_image.size
        logger.info(f"原始图像大小: {original_size}")
        
        # 转换为灰度图并调整大小，保持长宽比
        if input_image.mode != 'L':
            input_image = input_image.convert('L')
        
        # 计算调整后的尺寸，确保最长边为256，同时保持原始长宽比
        target_size = 256
        width, height = original_size
        if width > height:
            new_width = target_size
            new_height = int(height * (target_size / width))
        else:
            new_height = target_size
            new_width = int(width * (target_size / height))
            
        # 调整图像大小，保持原始长宽比
        resized_image = input_image.resize((new_width, new_height), Image.LANCZOS)
        
        # 创建正方形画布，并将调整后的图像放在中央
        square_image = Image.new('L', (target_size, target_size), 0)
        paste_x = (target_size - new_width) // 2
        paste_y = (target_size - new_height) // 2
        square_image.paste(resized_image, (paste_x, paste_y))
        
        # 转换为NumPy数组作为模型输入
        input_data = np.array(square_image)
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 保存原始上传图像
        original_image_dir = os.path.join("MRI", "app", "uploads", "originals")
        os.makedirs(original_image_dir, exist_ok=True)
        original_image_path = os.path.join(original_image_dir, f"{task_id}_original.png")
        input_image.save(original_image_path)
        
        # 保存预处理后的输入图像
        processed_image_path = os.path.join(original_image_dir, f"{task_id}.png")
        square_image.save(processed_image_path)
        
        # 使用模型进行预测
        start_time = datetime.now()
        result = model_service.predict(model_id, input_data)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # 将重建结果转换为图像
        reconstructed_image = result["reconstructed_image"]
        reconstructed_img = Image.fromarray((reconstructed_image * 255).astype(np.uint8))
        
        # 确保重建图像尺寸与预处理的输入图像相同
        if reconstructed_img.size != (target_size, target_size):
            logger.warning(f"重建图像尺寸不匹配，调整为目标尺寸 {target_size}x{target_size}")
            reconstructed_img = reconstructed_img.resize((target_size, target_size), Image.LANCZOS)
            
        # 转换为base64编码的图像
        buffered = io.BytesIO()
        reconstructed_img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # 保存重建结果图像
        reconstructed_image_dir = os.path.join("MRI", "app", "uploads", "reconstructed")
        os.makedirs(reconstructed_image_dir, exist_ok=True)
        reconstructed_image_path = os.path.join(reconstructed_image_dir, f"{task_id}.png")
        reconstructed_img.save(reconstructed_image_path)
        
        # 获取评估指标
        metrics = result["metrics"]
        
        # 保存重建历史记录
        try:
            # 获取模型名称
            model_name = None
            models = model_service.get_models_list()
            for model in models:
                if model.get("id") == model_id:
                    model_name = model.get("name")
                    break
            
            # 创建历史记录
            history_record = ReconstructionHistory(
                user_id=current_user.id,
                task_id=task_id,
                model_id=model_id,
                model_name=model_name,
                original_image_path=original_image_path,
                reconstructed_image_path=reconstructed_image_path,
                psnr=metrics.get("psnr"),
                ssim=metrics.get("ssim"),
                nse=metrics.get("nse"),
                execution_time=execution_time,
                status="completed",
                metrics=metrics
            )
            
            db.add(history_record)
            db.commit()
            db.refresh(history_record)
            logger.info(f"已保存重建历史记录，ID: {history_record.id}")
        except Exception as e:
            logger.error(f"保存重建历史记录时出错: {e}")
            # 继续处理，不中断响应
        
        return {
            "success": True,
            "message": "图像重建成功",
            "result_id": task_id,
            "reconstructed_image": img_str,
            "metrics": metrics,
            "execution_time": execution_time,
            "history_id": getattr(history_record, 'id', None)
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