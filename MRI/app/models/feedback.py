from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from MRI.app.models.user import Base

class Feedback(Base):
    """用户反馈模型"""
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum("pending", "processing", "resolved"), default="pending", nullable=False)
    reply = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    replied_at = Column(DateTime, nullable=True)
    
    # 添加与用户的关系
    user = relationship("User", back_populates="feedbacks") 