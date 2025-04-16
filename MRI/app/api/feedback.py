from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging

from MRI.app.services.db import get_db
from MRI.app.services.auth import get_current_user
from MRI.app.models.user import User
from MRI.app.models.feedback import Feedback
from MRI.app.schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackUpdate

# 创建日志记录器
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    tags=["反馈"],
    responses={404: {"description": "未找到"}},
)

# 创建反馈
@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback: FeedbackCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建用户反馈"""
    logger.info(f"用户 {current_user.username} 创建反馈: {feedback.title}")
    
    db_feedback = Feedback(
        title=feedback.title,
        content=feedback.content,
        user_id=current_user.id
    )
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    logger.info(f"反馈创建成功，ID: {db_feedback.id}")
    return db_feedback

# 获取所有反馈（管理员用）
@router.get("/all", response_model=List[FeedbackResponse])
async def get_all_feedbacks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """获取所有用户反馈（管理员专用）"""
    if current_user.role != "admin":
        logger.warning(f"非管理员用户 {current_user.username} 尝试访问所有反馈")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅管理员可查看所有反馈"
        )
    
    feedbacks = db.query(Feedback).order_by(Feedback.created_at.desc()).offset(skip).limit(limit).all()
    logger.info(f"管理员 {current_user.username} 获取所有反馈，数量: {len(feedbacks)}")
    return feedbacks

# 获取我的反馈
@router.get("/my", response_model=List[FeedbackResponse])
async def get_my_feedbacks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的反馈"""
    feedbacks = db.query(Feedback).filter(Feedback.user_id == current_user.id).order_by(Feedback.created_at.desc()).all()
    logger.info(f"用户 {current_user.username} 获取自己的反馈，数量: {len(feedbacks)}")
    return feedbacks

# 获取反馈详情
@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取反馈详情"""
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        logger.warning(f"反馈ID {feedback_id} 不存在")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="反馈不存在"
        )
    
    # 检查权限：只有管理员或反馈的创建者可以查看
    if current_user.role != "admin" and feedback.user_id != current_user.id:
        logger.warning(f"用户 {current_user.username} 尝试访问非自己创建的反馈 {feedback_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，您无法查看此反馈"
        )
    
    logger.info(f"用户 {current_user.username} 获取反馈详情，ID: {feedback_id}")
    return feedback

# 更新反馈（管理员回复）
@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: int,
    feedback_update: FeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新反馈状态和回复（管理员专用）"""
    if current_user.role != "admin":
        logger.warning(f"非管理员用户 {current_user.username} 尝试更新反馈")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅管理员可更新反馈"
        )
    
    db_feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not db_feedback:
        logger.warning(f"反馈ID {feedback_id} 不存在")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="反馈不存在"
        )
    
    # 更新状态
    if feedback_update.status:
        db_feedback.status = feedback_update.status
    
    # 更新回复
    if feedback_update.reply:
        db_feedback.reply = feedback_update.reply
        db_feedback.replied_at = datetime.now()
    
    db.commit()
    db.refresh(db_feedback)
    
    logger.info(f"管理员 {current_user.username} 更新反馈，ID: {feedback_id}, 状态: {db_feedback.status}")
    return db_feedback 