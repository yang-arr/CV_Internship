#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FastAPI主应用入口
包含应用初始化、路由配置、中间件设置等
"""

import os
from fastapi import FastAPI, HTTPException, Request, Depends, status, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Optional
# from jose import JWTError, jwt

# 获取当前文件的绝对路径
BASE_DIR = Path(__file__).resolve().parent

# 创建FastAPI实例
app = FastAPI(
    title="MRI重建系统",
    description="基于隐式神经表示（INR）的二维MRI图像重建系统",
    version="1.0.0"
)

# 配置静态文件目录
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 配置模板目录
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由和服务
from MRI.app.api import reconstruction, model_management, upload, websocket, auth, medical_qa, online_training, dashboard, reconstruction_history, medical_analysis, feedback
from MRI.app.services.db import create_tables, get_db
from MRI.app.services.auth import get_current_user, SECRET_KEY, ALGORITHM
from MRI.app.models.user import User

# 注册路由
app.include_router(reconstruction.router, prefix="/api/reconstruction", tags=["重建"])
app.include_router(model_management.router, prefix="/api/models", tags=["模型管理"])
app.include_router(upload.router, prefix="/api/upload", tags=["文件上传"])
app.include_router(websocket.router, prefix="/api", tags=["WebSocket"])
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(medical_qa.router, prefix="/api/medical", tags=["医疗问答"])
app.include_router(online_training.router, prefix="/api/online-training", tags=["在线训练"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["数据看板"])
app.include_router(reconstruction_history.router, prefix="/api/reconstruction-history", tags=["重建历史记录"])
app.include_router(medical_analysis.router, prefix="/api/medical-analysis", tags=["医学图像分析"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["反馈"])

# 启动事件
@app.on_event("startup")
async def startup():
    """应用启动时执行的操作"""
    # 创建数据库表
    create_tables()

# 自定义异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理HTTP异常"""
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        # 如果是认证失败，重定向到登录页面
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return {"detail": exc.detail}

# 根路由 - 重定向到仪表盘或登录页面
@app.get("/")
async def root(request: Request):
    """根路由重定向到仪表盘或登录页面"""
    # 直接重定向到仪表盘页面，仪表盘页面会自动验证用户是否登录
    # 如果未登录，dashboard_page会自动抛出异常并重定向到登录页面
    return RedirectResponse(url="/dashboard")

# 登录页面路由
@app.get("/login")
async def login_page(request: Request):
    """渲染登录页面"""
    try:
        # 如果用户已登录，直接重定向到仪表盘
        await get_current_user(request)
        return RedirectResponse(url="/dashboard")
    except HTTPException:
        # 如果用户未登录，显示登录页面
        return templates.TemplateResponse("login.html", {"request": request})

# 仪表盘页面路由
@app.get("/dashboard")
async def dashboard_page(request: Request, current_user: User = Depends(get_current_user)):
    """渲染仪表盘页面"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": current_user.username
    })

# 登出路由
@app.get("/logout")
async def logout():
    """用户登出"""
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    response.headers["Clear-Site-Data"] = '"storage"'  # 清除localStorage
    return response

# 注册页面路由
@app.get("/register")
async def register_page(request: Request):
    """渲染注册页面"""
    return templates.TemplateResponse("register.html", {"request": request})

# 重建页面路由 - 需要认证
@app.get("/reconstruction")
async def reconstruction_page(request: Request):
    """渲染重建页面，会自动由前端JS检查认证状态"""
    # 这里简单地渲染页面，认证检查由前端JavaScript处理
    # 前端脚本会在页面加载时检查localStorage中的token，如果无效会自动跳转到登录页面
    return templates.TemplateResponse("index.html", {"request": request})

# 医疗问答页面路由
@app.get("/medical-qa")
async def medical_qa_page(request: Request):
    """渲染医疗问答页面"""
    return templates.TemplateResponse("medical_qa.html", {"request": request})

# 在线训练页面路由
@app.get("/online-training")
async def online_training_page(request: Request):
    """渲染在线训练页面"""
    return templates.TemplateResponse("online_training.html", {"request": request})

# 数据看板页面路由
@app.get("/data-dashboard")
async def data_dashboard_page(request: Request, current_user: User = Depends(get_current_user)):
    """渲染数据看板页面"""
    return templates.TemplateResponse("data_dashboard.html", {
        "request": request,
        "username": current_user.username
    })

# 设置页面路由
@app.get("/settings")
async def settings_page(request: Request, current_user: User = Depends(get_current_user)):
    """渲染设置页面"""
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "username": current_user.username
    })

# 关于我们页面路由
@app.get("/about")
async def about_page(request: Request):
    """渲染关于我们页面"""
    return templates.TemplateResponse("about.html", {"request": request})

# 管理员控制台页面路由
@app.get("/admin")
async def admin_page(request: Request, current_user: User = Depends(get_current_user)):
    """渲染管理员控制台页面"""
    # 检查用户是否是管理员
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，仅管理员可访问此页面"
        )
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "username": current_user.username
    })

# 我的反馈页面路由
@app.get("/my-feedback")
async def my_feedback_page(request: Request, current_user: User = Depends(get_current_user)):
    """渲染我的反馈页面"""
    return templates.TemplateResponse("my_feedback.html", {
        "request": request,
        "username": current_user.username
    })

# 根路由 - API信息
@app.get("/api")
async def api_root():
    return {
        "name": "MRI重建系统API",
        "version": "1.0.0",
        "description": "基于隐式神经表示（INR）的二维MRI图像重建系统API服务"
    }

# 健康检查路由
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import sys
    from pathlib import Path
    # 将项目根目录添加到Python路径
    root_dir = str(Path(__file__).resolve().parent.parent.parent)
    if root_dir not in sys.path:
        sys.path.append(root_dir)
    
    import uvicorn
    uvicorn.run("MRI.app.main:app", host="127.0.0.1", port=8001, reload=True)