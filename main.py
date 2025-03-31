from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import image_router, user_router, websocket_router
from app.database.db import create_tables
import socket
import uvicorn

def get_local_ip():
    """获取本机内网IP地址"""
    try:
        # 创建一个临时socket连接来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# 创建FastAPI应用实例
app = FastAPI(
    title="图像处理API",
    description="用于图像上传、模型推理和结果返回的API",
    version="1.0.0"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 包含路由
app.include_router(user_router.router)
app.include_router(image_router.router)
app.include_router(websocket_router.router)

# 启动事件
@app.on_event("startup")
async def startup():
    # 创建数据库表
    create_tables()

# 根路由
@app.get("/")
async def root():
    return {"message": "Welcome Fast API!"}

# 启动应用的入口
if __name__ == "__main__":
    # 获取本机内网IP
    local_ip = get_local_ip()
    port = 8000
    
    print("\n" + "="*50)
    print(f"API服务已启动！")
    print(f"本地访问地址: http://127.0.0.1:{port}")
    print(f"局域网访问地址: http://{local_ip}:{port}")
    print(f"API文档地址: http://{local_ip}:{port}/docs")
    print("="*50 + "\n")
    
    # 启动服务器，监听所有网络接口
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)