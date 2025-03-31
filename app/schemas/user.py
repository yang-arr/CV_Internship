from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础信息模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="电子邮件")


class UserCreate(UserBase):
    """创建用户的请求模式"""
    password: str = Field(..., min_length=8, description="密码，最小长度为8")
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """验证用户名是否只包含字母和数字"""
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v


class UserLogin(BaseModel):
    """用户登录的请求模式"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(UserBase):
    """用户信息的响应模式"""
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    """更新用户信息的请求模式"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="电子邮件")
    password: Optional[str] = Field(None, min_length=8, description="密码，最小长度为8")


class Token(BaseModel):
    """访问令牌的响应模式"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """令牌数据的内部模式"""
    username: Optional[str] = None 