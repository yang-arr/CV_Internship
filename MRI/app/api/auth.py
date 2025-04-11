from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging
from fastapi.responses import RedirectResponse, JSONResponse

from MRI.app.services.db import get_db
from MRI.app.services.auth import (
    authenticate_user, create_access_token, 
    get_password_hash, get_current_user
)
from MRI.app.models.user import User
from MRI.app.schemas.user import UserCreate, UserResponse, Token

# 创建日志记录器
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/api/auth",
    tags=["认证"],
    responses={404: {"description": "未找到"}},
)

# 用户注册路由
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    logger.info(f"尝试注册用户: {user.username}")
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        logger.warning(f"注册失败，用户名已存在: {user.username}")
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    db_email = db.query(User).filter(User.email == user.email).first()
    if db_email:
        logger.warning(f"注册失败，邮箱已存在: {user.email}")
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
    
    logger.info(f"用户注册成功: {user.username}")
    return db_user

# 用户登录路由
@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db),
    response: Response = None
):
    """用户登录并获取访问令牌"""
    logger.info(f"尝试用户登录: {form_data.username}")
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"登录失败，用户名或密码不正确: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 创建访问令牌
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # 创建响应
    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "username": user.username
        }
    )
    
    # 设置cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,  # 30分钟
        expires=1800,
        samesite="lax",  # 添加 SameSite 属性
        secure=False  # 在生产环境中应该设置为 True
    )
    
    logger.info(f"用户登录成功，已生成令牌: {user.username}")
    return response

# 获取当前用户信息路由
@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    logger.info(f"获取用户信息: {current_user.username}")
    return current_user 