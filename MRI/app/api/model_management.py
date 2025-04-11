#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型管理API路由
处理模型管理相关的请求，如查询模型列表、模型详情等
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
from ..services.model_service import model_service
from datetime import datetime

from MRI.app.services.auth import get_current_user
from MRI.app.models.user import User

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 数据模型
class ModelInfo(BaseModel):
    """模型信息模型"""
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic配置"""
        # 允许额外的字段
        extra = "allow"

@router.get("/", response_model=List[ModelInfo])
async def list_models(current_user: User = Depends(get_current_user)):
    """
    获取所有可用的模型列表
    
    Returns:
        List[ModelInfo]: 模型信息列表
    """
    try:
        models = model_service.get_models_list()
        return models
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_id}", response_model=ModelInfo)
async def get_model_details(model_id: str = Path(..., title="模型ID"), current_user: User = Depends(get_current_user)):
    """
    获取指定模型的详细信息
    
    Args:
        model_id: 模型ID
        
    Returns:
        ModelInfo: 模型详细信息
    """
    try:
        model_info = model_service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
        
        # 添加ID字段到模型信息
        model_info["id"] = model_id
        
        return model_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model details for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_id}/performance", response_model=Dict[str, Any])
async def get_model_performance(model_id: str = Path(..., title="模型ID"), current_user: User = Depends(get_current_user)):
    """
    获取指定模型的性能指标
    
    Args:
        model_id: 模型ID
        
    Returns:
        Dict[str, Any]: 模型性能指标
    """
    try:
        # 检查模型是否存在
        model_info = model_service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
        
        # 使用专门的方法获取指标，此方法可能会从完整配置或内部存储中获取
        performance = model_service.get_model_metrics(model_id)
        
        return {"model_id": model_id, "performance": performance}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model performance for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_id}/original-image")
async def get_model_original_image(model_id: str = Path(..., title="模型ID"), current_user: User = Depends(get_current_user)):
    """
    获取指定模型训练时使用的原始图像
    
    Args:
        model_id: 模型ID
        
    Returns:
        Dict: 包含原始图像的base64编码
    """
    try:
        # 这里需要实现从模型目录中读取原始图像的逻辑
        # 暂时返回占位数据
        return {"model_id": model_id, "image_data": "base64_encoded_image_placeholder"}
    except Exception as e:
        logger.error(f"Error getting original image for model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 