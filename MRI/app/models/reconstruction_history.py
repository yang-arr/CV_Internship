#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
重建历史记录数据库模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
import datetime
from . import Base
from sqlalchemy.sql import func

class ReconstructionHistory(Base):
    """
    MRI重建历史记录模型
    """
    __tablename__ = "reconstruction_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(String(50), unique=True, index=True)
    model_id = Column(String(50), nullable=False)
    model_name = Column(String(100))
    original_image_path = Column(String(255))
    reconstructed_image_path = Column(String(255))
    psnr = Column(Float)
    ssim = Column(Float)
    nse = Column(Float)
    execution_time = Column(Float)
    created_at = Column(DateTime, default=func.now())
    status = Column(String(20), default="completed")  # 状态：completed, failed
    metrics = Column(JSON, nullable=True)  # 存储其他评估指标
    notes = Column(Text, nullable=True)  # 用户笔记
    
    # 关联用户
    user = relationship("User", back_populates="reconstruction_history")
    
    def __repr__(self):
        return f"<ReconstructionHistory(id={self.id}, user_id={self.user_id}, model_id={self.model_id})>" 