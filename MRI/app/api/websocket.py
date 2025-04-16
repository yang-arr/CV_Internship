#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WebSocket服务
用于实时通信，如重建进度更新、模型加载状态等
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from typing import Dict, List, Any, Optional
import json
import logging
import asyncio
from datetime import datetime
from jose import JWTError, jwt

from MRI.app.services.auth import SECRET_KEY, ALGORITHM

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 验证WebSocket令牌
async def get_token_data(token: str = Query(...)):
    """
    验证token并返回用户名
    
    Args:
        token: 认证令牌
        
    Returns:
        dict: 令牌数据
        
    Raises:
        HTTPException: 无效令牌时抛出
    """
    try:
        logger.info(f"验证WebSocket令牌: {token[:10]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("令牌中未找到用户名")
            return None
        logger.info(f"WebSocket令牌验证成功，用户: {username}")
        return {"username": username}
    except JWTError as e:
        logger.error(f"WebSocket令牌验证失败: {str(e)}")
        return None

# 连接管理器
class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        """初始化连接管理器"""
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """
        建立WebSocket连接
        
        Args:
            websocket: WebSocket连接
            client_id: 客户端ID
        """
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """
        断开WebSocket连接
        
        Args:
            websocket: WebSocket连接
            client_id: 客户端ID
        """
        if client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_message(self, message: Dict[str, Any], client_id: str):
        """
        向指定客户端发送消息
        
        Args:
            message: 消息内容
            client_id: 客户端ID
        """
        if client_id in self.active_connections:
            disconnected_websockets = []
            for websocket in self.active_connections[client_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to client {client_id}: {e}")
                    disconnected_websockets.append(websocket)
            
            # 清理断开的连接
            for websocket in disconnected_websockets:
                self.disconnect(websocket, client_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        广播消息给所有客户端
        
        Args:
            message: 消息内容
        """
        for client_id in list(self.active_connections.keys()):
            await self.send_message(message, client_id)

# 创建连接管理器实例
manager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: str = Query(None)):
    """
    WebSocket端点
    
    Args:
        websocket: WebSocket连接
        client_id: 客户端ID
        token: 认证令牌
    """
    logger.info(f"收到WebSocket连接请求: client_id={client_id}")
    
    if not token:
        logger.warning(f"WebSocket连接无令牌，拒绝连接: client_id={client_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="未提供认证令牌")
        return
    
    # 验证令牌
    token_data = await get_token_data(token)
    if not token_data:
        logger.warning(f"WebSocket连接令牌无效，拒绝连接: client_id={client_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="无效的认证令牌")
        return
    
    try:
        await manager.connect(websocket, client_id)
        
        # 发送连接成功消息
        await manager.send_message(
            {
                "type": "connection_established",
                "client_id": client_id,
                "username": token_data.get("username"),
                "timestamp": datetime.now().isoformat(),
                "message": "Connection established"
            },
            client_id
        )
        
        logger.info(f"WebSocket连接已建立: client_id={client_id}, username={token_data.get('username')}")
        
        try:
            while True:
                # 接收消息
                data = await websocket.receive_text()
                
                try:
                    # 解析JSON消息
                    message = json.loads(data)
                    
                    # 处理消息
                    response = {
                        "type": "response",
                        "timestamp": datetime.now().isoformat(),
                        "original_message": message
                    }
                    
                    # 如果是ping消息，返回pong
                    if message.get("type") == "ping":
                        response["type"] = "pong"
                    
                    # 返回响应
                    await manager.send_message(response, client_id)
                    
                except json.JSONDecodeError:
                    # 非JSON消息
                    await manager.send_message(
                        {
                            "type": "error",
                            "timestamp": datetime.now().isoformat(),
                            "message": "Invalid JSON format"
                        },
                        client_id
                    )
        
        except WebSocketDisconnect:
            # 客户端断开连接
            logger.info(f"WebSocket客户端断开连接: client_id={client_id}")
            manager.disconnect(websocket, client_id)
        
    except Exception as e:
        # 其他异常
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(websocket, client_id)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass

# 用于外部调用的函数
async def send_progress_update(client_id: str, task_id: str, progress: float, status: str, message: str = ""):
    """
    发送进度更新消息
    
    Args:
        client_id: 客户端ID
        task_id: 任务ID
        progress: 进度值(0-100)
        status: 状态（'processing', 'completed', 'failed'）
        message: 状态消息
    """
    await manager.send_message(
        {
            "type": "progress_update",
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "progress": progress,
            "status": status,
            "message": message
        },
        client_id
    )

async def send_model_loaded(client_id: str, model_id: str, success: bool, message: str = ""):
    """
    发送模型加载状态消息
    
    Args:
        client_id: 客户端ID
        model_id: 模型ID
        success: 是否成功
        message: 状态消息
    """
    await manager.send_message(
        {
            "type": "model_loaded",
            "timestamp": datetime.now().isoformat(),
            "model_id": model_id,
            "success": success,
            "message": message
        },
        client_id
    )

async def send_reconstruction_complete(client_id: str, task_id: str, result_id: str, message: str = ""):
    """
    发送重建完成消息
    
    Args:
        client_id: 客户端ID
        task_id: 任务ID
        result_id: 结果ID
        message: 状态消息
    """
    await manager.send_message(
        {
            "type": "reconstruction_complete",
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "result_id": result_id,
            "message": message
        },
        client_id
    ) 