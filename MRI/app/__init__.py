"""
MRI重建系统主模块
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .api.reconstruction import router as reconstruction_router
from .api.model_management import router as model_management_router
from .api.training import router as training_router
from .api.auth import router as auth_router
from .routers import web_router

def create_app():
    app = FastAPI(title="MRI重建系统")
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 挂载静态文件
    app.mount("/static", StaticFiles(directory="MRI/app/static"), name="static")

    # 注册路由
    app.include_router(reconstruction_router, prefix="/api/reconstruction")
    app.include_router(model_management_router, prefix="/api/models")
    app.include_router(training_router, prefix="/api/training")
    app.include_router(auth_router, prefix="/api/auth")  # 添加认证路由
    app.include_router(web_router)  # Web页面路由

    return app 