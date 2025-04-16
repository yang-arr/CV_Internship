from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # 添加用户角色字段，默认为普通用户
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 添加用户与重建历史的关系
    reconstruction_history = relationship("ReconstructionHistory", back_populates="user", cascade="all, delete-orphan")
    
    # 添加用户与反馈的关系
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan") 