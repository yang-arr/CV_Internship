#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据看板API
提供系统数据统计、使用情况和性能监控
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime, timedelta
import json
import os
import logging
import psutil
import socket
import time
import platform
from typing import Dict, List, Any, Optional

from MRI.app.services.db import get_db
from MRI.app.services.auth import get_current_user
from MRI.app.models.user import User
from MRI.app.models.chat_history import ChatHistory, ChatMessage
from MRI.app.models.reconstruction_history import ReconstructionHistory
from MRI.app.services.model_service import model_service

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 安全地获取系统性能指标的辅助函数
def get_cpu_usage():
    """安全地获取CPU使用率"""
    try:
        return int(psutil.cpu_percent(interval=0.1))
    except Exception as e:
        logger.warning(f"获取CPU使用率失败: {str(e)}")
        return 30  # 返回默认值

def get_memory_usage():
    """安全地获取内存使用率"""
    try:
        memory = psutil.virtual_memory()
        return int(memory.percent)
    except Exception as e:
        logger.warning(f"获取内存使用率失败: {str(e)}")
        return 40  # 返回默认值

def get_disk_usage():
    """安全地获取磁盘使用率"""
    try:
        # 使用当前工作目录，避免使用根目录可能导致的权限问题
        disk = psutil.disk_usage(os.getcwd())
        return int(disk.percent)
    except Exception as e:
        logger.warning(f"获取磁盘使用率失败: {str(e)}")
        return 35  # 返回默认值

@router.get("/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    获取数据看板统计信息
    
    返回系统模型数量、重建图像数量、问答数量等统计信息
    """
    try:
        # 获取模型数量
        models = model_service.get_models_list()
        models_count = len(models)
        
        # 获取问答统计数据
        # 总问答会话数
        total_qa_sessions = db.query(func.count(distinct(ChatHistory.id))).scalar() or 0
        
        # 今日问答会话数
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_qa_sessions = db.query(func.count(distinct(ChatHistory.id))).filter(
            ChatHistory.created_at >= today_start
        ).scalar() or 0
        
        # 本周问答会话数
        week_start = datetime.now() - timedelta(days=7)
        week_qa_sessions = db.query(func.count(distinct(ChatHistory.id))).filter(
            ChatHistory.created_at >= week_start
        ).scalar() or 0
        
        # 获取活跃用户数据
        # 总用户数
        total_users = db.query(func.count(distinct(User.id))).scalar() or 0
        
        # 今日活跃用户数
        today_active_users = db.query(func.count(distinct(ChatHistory.user_id))).filter(
            ChatHistory.updated_at >= today_start
        ).scalar() or 0
        
        # 本周活跃用户数
        week_active_users = db.query(func.count(distinct(ChatHistory.user_id))).filter(
            ChatHistory.updated_at >= week_start
        ).scalar() or 0
        
        # 获取问答趋势数据（最近7天）
        qa_trend = []
        for i in range(6, -1, -1):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            daily_count = db.query(func.count(distinct(ChatHistory.id))).filter(
                ChatHistory.created_at >= day_start,
                ChatHistory.created_at < day_end
            ).scalar() or 0
            
            qa_trend.append({"date": date_str, "count": daily_count})
        
        # 获取系统性能指标 - 使用辅助函数分别获取
        cpu_usage = get_cpu_usage()
        memory_usage = get_memory_usage()
        disk_usage = get_disk_usage()
        
        # 平均响应时间 - 这里使用固定值，实际应用中可以从监控系统获取
        avg_response_time = 0.87
        
        # 获取重建历史记录统计数据
        # 总重建数
        total_reconstructions = db.query(func.count(ReconstructionHistory.id)).scalar() or 0
        
        # 今日重建数
        today_reconstructions = db.query(func.count(ReconstructionHistory.id)).filter(
            ReconstructionHistory.created_at >= today_start
        ).scalar() or 0
        
        # 本周重建数
        week_reconstructions = db.query(func.count(ReconstructionHistory.id)).filter(
            ReconstructionHistory.created_at >= week_start
        ).scalar() or 0
        
        # 重建趋势数据（最近7天）
        reconstruction_trend = []
        for i in range(6, -1, -1):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            daily_count = db.query(func.count(ReconstructionHistory.id)).filter(
                ReconstructionHistory.created_at >= day_start,
                ReconstructionHistory.created_at < day_end
            ).scalar() or 0
            
            reconstruction_trend.append({"date": date_str, "count": daily_count})
        
        stats = {
            "models_count": models_count,
            "reconstructions": {
                "total": total_reconstructions,
                "today": today_reconstructions,
                "week": week_reconstructions
            },
            "qa_sessions": {
                "total": total_qa_sessions,
                "today": today_qa_sessions,
                "week": week_qa_sessions
            },
            "active_users": {
                "total": total_users,
                "today": today_active_users,
                "week": week_active_users
            },
            "system_performance": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "avg_response_time": avg_response_time
            },
            "reconstruction_trend": reconstruction_trend,
            "qa_trend": qa_trend
        }
        
        logger.info("成功获取数据看板统计信息")
        # 直接返回字典，让FastAPI处理响应
        return stats
    except Exception as e:
        logger.error(f"获取数据看板统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/recent-reconstructions")
async def get_recent_reconstructions(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取最近的重建记录
    
    Args:
        limit: 返回记录的最大数量
    """
    try:
        # 查询最近的重建历史记录
        recent_history = db.query(ReconstructionHistory).order_by(
            ReconstructionHistory.created_at.desc()
        ).limit(limit).all()
        
        # 格式化记录
        recent_recs = []
        for record in recent_history:
            # 获取用户信息
            user = db.query(User).filter(User.id == record.user_id).first()
            username = user.username if user else "未知用户"
            
            # 添加记录
            recent_recs.append({
                "id": record.id,
                "user": username,
                "model": record.model_name or record.model_id,
                "timestamp": record.created_at.isoformat(),
                "execution_time": record.execution_time if record.execution_time is not None else 0.0,
                "metrics": {
                    "psnr": record.psnr,
                    "ssim": record.ssim,
                    "nse": record.nse
                }
            })
        
        logger.info(f"成功获取最近{len(recent_recs)}条重建记录")
        # 直接返回字典，让FastAPI处理响应
        return {"reconstructions": recent_recs}
    except Exception as e:
        logger.error(f"获取最近重建记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取重建记录失败: {str(e)}")

@router.get("/recent-qa")
async def get_recent_qa(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取最近的问答记录
    
    Args:
        limit: 返回记录的最大数量
    """
    try:
        # 从数据库中查询最近的问答记录
        # 先查询用户问题消息
        user_messages = db.query(ChatMessage).filter(
            ChatMessage.is_user == True
        ).order_by(
            ChatMessage.created_at.desc()
        ).limit(limit).all()
        
        recent_qa = []
        for msg in user_messages:
            # 获取此消息所属的ChatHistory
            chat_history = db.query(ChatHistory).filter(
                ChatHistory.id == msg.chat_history_id
            ).first()
            
            if chat_history:
                # 获取用户信息
                user = db.query(User).filter(
                    User.id == chat_history.user_id
                ).first()
                
                username = user.username if user else "未知用户"
                
                recent_qa.append({
                    "id": f"qa_{msg.id}",
                    "user": username,
                    "question": msg.content,
                    "timestamp": msg.created_at.isoformat()
                })
        
        logger.info(f"成功获取最近{len(recent_qa)}条问答记录")
        # 直接返回字典，让FastAPI处理响应
        return {"qa_records": recent_qa}
    except Exception as e:
        logger.error(f"获取最近问答记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取问答记录失败: {str(e)}")

@router.get("/reconstruction/{history_id}")
async def get_reconstruction_detail(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取特定重建历史记录的详细信息
    
    Args:
        history_id: 历史记录ID
    """
    try:
        # 查询特定的重建历史记录
        record = db.query(ReconstructionHistory).filter(
            ReconstructionHistory.id == history_id
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="未找到指定的重建记录")
        
        # 获取用户信息
        user = db.query(User).filter(User.id == record.user_id).first()
        username = user.username if user else "未知用户"
        
        # 构建返回数据
        detail = {
            "id": record.id,
            "user": username,
            "user_id": record.user_id,
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
            "notes": record.notes
        }
        
        logger.info(f"成功获取重建记录详情: ID={history_id}")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取重建记录详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取重建记录详情失败: {str(e)}") 