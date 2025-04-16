#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
重建历史记录API
提供MRI重建历史记录的增删改查功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
from sqlalchemy.orm import Session
import os
import uuid
from datetime import datetime
import json
from pydantic import BaseModel

from MRI.app.services.db import get_db
from MRI.app.services.auth import get_current_user
from MRI.app.models.reconstruction_history import ReconstructionHistory
from MRI.app.models.user import User

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 历史记录分页查询参数模型
class HistoryQueryParams(BaseModel):
    page: int = 1
    page_size: int = 10
    user_id: Optional[int] = None
    model_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"

# 历史记录笔记更新模型
class HistoryNoteUpdate(BaseModel):
    notes: str

# 获取当前用户的重建历史记录
@router.get("/")
async def get_reconstruction_history(
    page: int = 1,
    page_size: int = 10,
    model_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的重建历史记录，支持分页和筛选"""
    try:
        logger.info(f"获取用户 {current_user.id} 的重建历史记录")
        
        # 构建查询
        query = db.query(ReconstructionHistory).filter(ReconstructionHistory.user_id == current_user.id)
        
        # 应用筛选
        if model_id:
            query = query.filter(ReconstructionHistory.model_id == model_id)
            
        if start_date:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(ReconstructionHistory.created_at >= start_datetime)
            
        if end_date:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(ReconstructionHistory.created_at <= end_datetime)
        
        # 获取总记录数
        total_count = query.count()
        
        # 排序和分页
        query = query.order_by(ReconstructionHistory.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # 执行查询
        history_records = query.all()
        
        # 构建结果
        result = []
        for record in history_records:
            result.append({
                "id": record.id,
                "task_id": record.task_id,
                "model_id": record.model_id,
                "model_name": record.model_name,
                "psnr": record.psnr,
                "ssim": record.ssim,
                "nse": record.nse,
                "execution_time": record.execution_time,
                "created_at": record.created_at.isoformat(),
                "status": record.status,
                "notes": record.notes
            })
        
        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "records": result
        }
    except Exception as e:
        logger.error(f"获取重建历史记录时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")

# 获取历史记录详情
@router.get("/{history_id}")
async def get_reconstruction_history_detail(
    history_id: int = Path(..., title="历史记录ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取重建历史记录详情"""
    try:
        # 查询记录
        record = db.query(ReconstructionHistory).filter(
            ReconstructionHistory.id == history_id,
            ReconstructionHistory.user_id == current_user.id
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="未找到指定的历史记录")
        
        # 构建响应
        return {
            "id": record.id,
            "task_id": record.task_id,
            "model_id": record.model_id,
            "model_name": record.model_name,
            "original_image_path": record.original_image_path,
            "reconstructed_image_path": record.reconstructed_image_path,
            "psnr": record.psnr,
            "ssim": record.ssim,
            "nse": record.nse,
            "execution_time": record.execution_time,
            "created_at": record.created_at.isoformat(),
            "status": record.status,
            "metrics": record.metrics,
            "notes": record.notes
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史记录详情时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史记录详情失败: {str(e)}")

# 添加重建历史记录
@router.post("/")
async def create_reconstruction_history(
    task_id: str = Body(...),
    model_id: str = Body(...),
    model_name: Optional[str] = Body(None),
    original_image_path: Optional[str] = Body(None),
    reconstructed_image_path: Optional[str] = Body(None),
    psnr: Optional[float] = Body(None),
    ssim: Optional[float] = Body(None),
    nse: Optional[float] = Body(None),
    execution_time: Optional[float] = Body(None),
    status: str = Body("completed"),
    metrics: Optional[Dict[str, Any]] = Body(None),
    notes: Optional[str] = Body(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建重建历史记录"""
    try:
        # 创建记录
        new_record = ReconstructionHistory(
            user_id=current_user.id,
            task_id=task_id,
            model_id=model_id,
            model_name=model_name,
            original_image_path=original_image_path,
            reconstructed_image_path=reconstructed_image_path,
            psnr=psnr,
            ssim=ssim,
            nse=nse,
            execution_time=execution_time,
            status=status,
            metrics=metrics,
            notes=notes
        )
        
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        
        return {
            "success": True,
            "message": "历史记录创建成功",
            "id": new_record.id
        }
    except Exception as e:
        db.rollback()
        logger.error(f"创建历史记录时出错: {e}")
        raise HTTPException(status_code=500, detail=f"创建历史记录失败: {str(e)}")

# 更新历史记录笔记
@router.patch("/{history_id}/notes")
async def update_reconstruction_history_notes(
    history_id: int = Path(..., title="历史记录ID"),
    note_update: HistoryNoteUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新历史记录的笔记"""
    try:
        # 查询记录
        record = db.query(ReconstructionHistory).filter(
            ReconstructionHistory.id == history_id,
            ReconstructionHistory.user_id == current_user.id
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="未找到指定的历史记录")
        
        # 更新笔记
        record.notes = note_update.notes
        db.commit()
        
        return {
            "success": True,
            "message": "历史记录笔记更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新历史记录笔记时出错: {e}")
        raise HTTPException(status_code=500, detail=f"更新历史记录笔记失败: {str(e)}")

# 删除历史记录
@router.delete("/{history_id}")
async def delete_reconstruction_history(
    history_id: int = Path(..., title="历史记录ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除历史记录"""
    try:
        # 查询记录
        record = db.query(ReconstructionHistory).filter(
            ReconstructionHistory.id == history_id,
            ReconstructionHistory.user_id == current_user.id
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="未找到指定的历史记录")
        
        # 删除记录
        db.delete(record)
        db.commit()
        
        return {
            "success": True,
            "message": "历史记录删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除历史记录时出错: {e}")
        raise HTTPException(status_code=500, detail=f"删除历史记录失败: {str(e)}") 