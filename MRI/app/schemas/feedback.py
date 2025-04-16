from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FeedbackBase(BaseModel):
    """反馈基础模型"""
    title: str
    content: str

class FeedbackCreate(FeedbackBase):
    """创建反馈请求模型"""
    pass

class FeedbackUpdate(BaseModel):
    """更新反馈请求模型"""
    status: Optional[str] = None
    reply: Optional[str] = None

class FeedbackResponse(FeedbackBase):
    """反馈响应模型"""
    id: int
    user_id: int
    status: str
    reply: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    replied_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True 