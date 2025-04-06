from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
import json
from typing import Dict, List, Any
import asyncio
from datetime import datetime

from MRI.appDatas.appDatabase.routers.image_router import inference_tasks
from MRI.appDatas.appDatabase.database.db import get_db
from jose import JWTError, jwt
from MRI.appDatas.appDatabase.routers.user_router import SECRET_KEY, ALGORITHM

# 创建路由器
router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
)

# 创建日志记录器
logger = logging.getLogger("websocket_router")

# 连接管理器
class ConnectionManager:
    def __init__(self):
        # 使用字典存储WebSocket连接，按用户ID分组
        self.active_connections: Dict[int, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int):
        """
        建立新的WebSocket连接
        
        Args:
            websocket (WebSocket): WebSocket连接对象
            user_id (int): 用户ID
        """
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket连接已建立: 用户ID={user_id}")
        
    def disconnect(self, websocket: WebSocket, user_id: int):
        """
        关闭WebSocket连接
        
        Args:
            websocket (WebSocket): WebSocket连接对象
            user_id (int): 用户ID
        """
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket连接已关闭: 用户ID={user_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], user_id: int):
        """
        向特定用户发送消息
        
        Args:
            message (Dict[str, Any]): 消息内容
            user_id (int): 用户ID
        """
        if user_id in self.active_connections:
            # 获取当前时间
            message["timestamp"] = datetime.now().isoformat()
            
            # 转换为JSON字符串
            message_str = json.dumps(message)
            
            # 向用户的所有活跃连接发送消息
            disconnected_websockets = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.error(f"发送消息失败: {str(e)}")
                    disconnected_websockets.append(websocket)
            
            # 移除断开的连接
            for websocket in disconnected_websockets:
                self.disconnect(websocket, user_id)


# 创建连接管理器实例
manager = ConnectionManager()


# 监控推理任务状态的后台任务
async def monitor_inference_tasks():
    """持续监控推理任务状态，并通过WebSocket发送更新"""
    while True:
        for task_id, task in list(inference_tasks.items()):
            # 如果任务状态发生变化（完成或失败）且通知标志未设置
            if (task["status"] in ["completed", "failed"]) and not task.get("notified", False):
                # 构造消息
                message = {
                    "type": "inference_task_update",
                    "task_id": task_id,
                    "status": task["status"],
                    "image_id": task["image_id"]
                }
                
                # 添加结果URL（如果有）
                if "result_url" in task:
                    message["result_url"] = task["result_url"]
                
                # 添加错误信息（如果有）
                if "error" in task:
                    message["error"] = task["error"]
                
                # 向用户发送消息
                await manager.send_personal_message(message, task["user_id"])
                
                # 设置通知标志
                task["notified"] = True
                
                logger.info(f"通过WebSocket发送任务状态更新: {task_id}, 状态={task['status']}")
        
        # 等待一段时间再检查
        await asyncio.sleep(1)


# 解析JWT令牌获取用户ID
async def get_user_id_from_token(token: str) -> int:
    """
    从JWT令牌中获取用户ID
    
    Args:
        token (str): JWT令牌
        
    Returns:
        int: 用户ID
        
    Raises:
        HTTPException: 如果令牌无效
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的认证凭据")
        return payload.get("user_id")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的认证凭据")


@router.websocket("/inference")
async def websocket_inference(websocket: WebSocket, token: str = None):
    """
    WebSocket端点，用于推理任务的实时更新
    
    客户端连接示例:
    ws://example.com/ws/inference?token=YOUR_JWT_TOKEN
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        # 验证令牌并获取用户ID
        user_id = await get_user_id_from_token(token)
        
        # 建立连接
        await manager.connect(websocket, user_id)
        
        # 发送欢迎消息
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "已连接到推理任务的WebSocket更新服务",
            "timestamp": datetime.now().isoformat()
        }))
        
        # 启动监控任务（如果尚未启动）
        if not hasattr(monitor_inference_tasks, "is_running"):
            asyncio.create_task(monitor_inference_tasks())
            setattr(monitor_inference_tasks, "is_running", True)
            logger.info("推理任务监控已启动")
        
        # 等待消息（主要是为了保持连接）
        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 简单的echo回复
                await websocket.send_text(json.dumps({
                    "type": "echo",
                    "content": message,
                    "timestamp": datetime.now().isoformat()
                }))
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
        
    except HTTPException as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    except Exception as e:
        logger.error(f"WebSocket处理中发生错误: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR) 