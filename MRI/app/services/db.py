import os
import logging
import configparser
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from MRI.app.models import Base

# 创建日志记录器
logger = logging.getLogger("db")

# 读取配置文件
config = configparser.ConfigParser()
config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'appDatas', 'config.ini')

# 默认数据库配置
DB_USER = "dvlp"
DB_PASSWORD = "passwd"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "mission1_db"

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

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 获取数据库会话的依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 创建所有表
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"创建数据库表时出错: {e}")
        raise 