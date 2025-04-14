import os
import logging
import configparser
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header, Cookie, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from MRI.app.services.db import get_db
from MRI.app.models.user import User
from MRI.app.schemas.user import TokenData

# 创建日志记录器
logger = logging.getLogger("auth_service")

# 读取配置文件
config = configparser.ConfigParser()
config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'appDatas', 'config.ini')

# JWT配置
SECRET_KEY = "your_secret_key_for_jwt"  # 默认密钥
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 如果存在配置文件，则读取密钥
if os.path.exists(config_file):
    config.read(config_file)
    if 'app' in config:
        SECRET_KEY = config['app'].get('SECRET_KEY', SECRET_KEY)
    
logger.info(f"已加载认证配置，过期时间: {ACCESS_TOKEN_EXPIRE_MINUTES}分钟")

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2密码Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    """用户认证"""
    logger.info(f"尝试认证用户: {username}")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"认证失败，用户不存在: {username}")
        return False
    if not verify_password(password, user.hashed_password):
        logger.warning(f"认证失败，密码不正确: {username}")
        return False
    logger.info(f"用户认证成功: {username}")
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"为用户创建访问令牌: {data.get('sub')}, 过期时间: {expire}")
    return encoded_jwt


async def get_token_from_cookie_or_header(
    request: Request,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
) -> Optional[str]:
    """从Cookie或Authorization头中获取令牌"""
    logger.info("尝试从Cookie或Header获取令牌")
    
    # 首先尝试从cookie获取
    if access_token and isinstance(access_token, str):
        logger.info("从Cookie获取到令牌")
        if access_token.startswith("Bearer "):
            return access_token.replace("Bearer ", "")
        return access_token
    
    # 然后尝试从header获取
    if authorization and isinstance(authorization, str):
        logger.info("从Header获取到令牌")
        if authorization.startswith("Bearer "):
            return authorization.replace("Bearer ", "")
        return authorization
    
    logger.warning("未找到令牌")
    return None


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(get_token_from_cookie_or_header)
):
    """获取当前用户"""
    logger.info("验证当前用户令牌")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的身份认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        logger.warning("未找到认证令牌")
        raise credentials_exception
        # 确保token是字符串类型
    if not isinstance(token, str):
        logger.warning(f"令牌类型错误: {type(token).__name__}")
        raise credentials_exception

    try:
        # 解码令牌
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("令牌中未找到用户名")
            raise credentials_exception
        token_data = TokenData(username=username)
        logger.info(f"令牌有效，用户名: {username}")
    except JWTError as e:
        logger.error(f"解码令牌失败: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"处理令牌时发生未知错误: {str(e)}")
        raise credentials_exception
        
    # 查询用户
    user = db.query(User).filter(User.username == token_data.username).first()
    
    if user is None:
        logger.warning(f"令牌中的用户不存在: {token_data.username}")
        raise credentials_exception
    
    logger.info(f"当前用户验证成功: {user.username}")
    return user 