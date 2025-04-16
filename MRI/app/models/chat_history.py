from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from MRI.app.models.user import Base

class ChatHistory(Base):
    """聊天历史记录模型"""
    __tablename__ = "chat_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)  # 会话标题，默认使用第一条消息作为标题
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    user = relationship("User", backref="chat_histories")
    messages = relationship("ChatMessage", back_populates="chat_history", cascade="all, delete-orphan")


class ChatMessage(Base):
    """聊天消息模型"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_history_id = Column(Integer, ForeignKey("chat_histories.id"), nullable=False)
    content = Column(Text, nullable=False)  # 消息内容
    is_user = Column(Boolean, default=True)  # 是否是用户消息，False表示AI回复
    sequence = Column(Integer, nullable=False)  # 消息序号，用于排序
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联关系
    chat_history = relationship("ChatHistory", back_populates="messages") 