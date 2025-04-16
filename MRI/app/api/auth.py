from fastapi import APIRouter, Depends, HTTPException, status, Response, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging
from fastapi.responses import RedirectResponse, JSONResponse

from MRI.app.services.db import get_db
from MRI.app.services.auth import (
    authenticate_user, create_access_token, 
    get_password_hash, get_current_user, create_access_token_with_role
)
from MRI.app.models.user import User
from MRI.app.schemas.user import UserCreate, UserResponse, Token

# 创建日志记录器
logger = logging.getLogger(__name__)

# 创建路由器 - 移除前缀，因为它在main.py中已添加
router = APIRouter(
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
        hashed_password=get_password_hash(user.password),
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"用户注册成功: {user.username}, 角色: {user.role}")
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
    access_token = create_access_token_with_role(
        user=user, expires_delta=access_token_expires
    )
    
    # 创建响应
    token_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role
    }
    
    response = JSONResponse(
        content=token_data
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
    
    logger.info(f"用户登录成功，已生成令牌: {user.username}, 角色: {user.role}")
    return response

# 获取当前用户信息路由
@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    logger.info(f"获取用户信息: {current_user.username}")
    return current_user

# 获取所有用户（仅管理员可访问）
@router.get("/users", response_model=list[UserResponse])
async def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取所有用户（仅管理员可访问）"""
    # 检查用户是否是管理员
    if current_user.role != "admin":
        logger.warning(f"非管理员用户 {current_user.username} 尝试访问所有用户信息")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅管理员可查看所有用户信息"
        )
    
    users = db.query(User).all()
    logger.info(f"管理员 {current_user.username} 获取所有用户信息，数量: {len(users)}")
    return users

# 更新用户角色（仅管理员可访问）
@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户角色（仅管理员可访问）"""
    # 检查用户是否是管理员
    if current_user.role != "admin":
        logger.warning(f"非管理员用户 {current_user.username} 尝试修改用户角色")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅管理员可修改用户角色"
        )
    
    # 检查角色是否有效
    if role not in ["user", "admin"]:
        logger.warning(f"管理员 {current_user.username} 尝试设置无效的用户角色: {role}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户角色，仅支持'user'或'admin'"
        )
    
    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"管理员 {current_user.username} 尝试修改不存在的用户 ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新用户角色
    user.role = role
    db.commit()
    db.refresh(user)
    
    logger.info(f"管理员 {current_user.username} 将用户 {user.username} 的角色修改为 {role}")
    return user 