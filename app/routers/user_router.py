from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

from app.schemas import UserCreate, UserResponse, UserUpdate, Token, TokenData
from app.database.db import User, get_db
from app.utils.exceptions import AuthenticationException, ResourceNotFoundException

# 加载环境变量
load_dotenv()

# 创建路由器
router = APIRouter(
    prefix="/users",
    tags=["用户"],
    responses={404: {"description": "未找到"}},
)

# 创建日志记录器
logger = logging.getLogger("user_router")

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2密码Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-jwt")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password, hashed_password):
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """哈希密码"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str):
    """认证用户"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """从令牌获取当前用户"""
    credentials_exception = AuthenticationException(detail="无效的认证凭据")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录并获取访问令牌"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise AuthenticationException(detail="用户名或密码不正确")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """创建新用户"""
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    db_email = db.query(User).filter(User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 创建用户
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"创建用户成功: {user.username}")
    return db_user


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    # 如果更新用户名
    if user_update.username and user_update.username != current_user.username:
        # 检查用户名是否已存在
        db_user = db.query(User).filter(User.username == user_update.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="用户名已存在")
        current_user.username = user_update.username
    
    # 如果更新邮箱
    if user_update.email and user_update.email != current_user.email:
        # 检查邮箱是否已存在
        db_email = db.query(User).filter(User.email == user_update.email).first()
        if db_email:
            raise HTTPException(status_code=400, detail="邮箱已存在")
        current_user.email = user_update.email
    
    # 如果更新密码
    if user_update.password:
        current_user.hashed_password = get_password_hash(user_update.password)
    
    current_user.updated_at = datetime.now()
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"更新用户信息成功: {current_user.username}")
    return current_user 