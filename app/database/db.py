import os
import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import configparser
from typing import Optional

# 创建日志记录器
logger = logging.getLogger("db")

# 读取配置文件（如果存在的话）
config = configparser.ConfigParser()
config_file = 'config.ini'

# 默认数据库配置
DB_USER = "root"
DB_PASSWORD = ""
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "image_processing"

# 如果存在配置文件，则从文件中读取数据库配置
if os.path.exists(config_file):
    config.read(config_file)
    if 'database' in config:
        DB_USER = config['database'].get('DB_USER', DB_USER)
        DB_PASSWORD = config['database'].get('DB_PASSWORD', DB_PASSWORD)
        DB_HOST = config['database'].get('DB_HOST', DB_HOST)
        DB_PORT = config['database'].get('DB_PORT', DB_PORT)
        DB_NAME = config['database'].get('DB_NAME', DB_NAME)

# 构建数据库URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 创建数据库引擎
try:
    engine = create_engine(DATABASE_URL)
    logger.info("数据库连接成功")
except Exception as e:
    logger.error(f"数据库连接错误: {e}")
    raise

# 创建基类
Base = declarative_base()

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 获取数据库会话的依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 用户模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    images = relationship("Image", back_populates="user")

# 图像模型
class Image(Base):
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String(255), nullable=False)
    original_path = Column(String(255), nullable=False)  # 原始图像路径
    processed_path = Column(String(255), nullable=True)  # 处理后图像路径（如有）
    file_size = Column(Integer)  # 文件大小（字节）
    mime_type = Column(String(100))  # 文件类型
    width = Column(Integer, nullable=True)  # 图像宽度
    height = Column(Integer, nullable=True)  # 图像高度
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    user = relationship("User", back_populates="images")
    results = relationship("InferenceResult", back_populates="image")

# 推理结果模型
class InferenceResult(Base):
    __tablename__ = "inference_results"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"))
    model_name = Column(String(100))  # 使用的模型名称
    result_data = Column(Text, nullable=True)  # JSON格式的结果数据
    confidence = Column(Float, nullable=True)  # 置信度
    processing_time = Column(Float, nullable=True)  # 处理时间（秒）
    status = Column(String(50), default="pending")  # 状态：pending, processing, completed, failed
    error_message = Column(Text, nullable=True)  # 错误信息（如果有）
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    image = relationship("Image", back_populates="results")

# 创建所有表
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"创建数据库表时出错: {e}")
        raise 