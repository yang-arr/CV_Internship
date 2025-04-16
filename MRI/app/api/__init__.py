"""
MRI重建系统API模块
包含以下路由：
- reconstruction: 重建相关API
- model_management: 模型管理API
- upload: 文件上传API
- websocket: WebSocket API
- auth: 用户认证API
- online_training: 在线训练API
- reconstruction_history: 重建历史记录API
- medical_analysis: 医学图像分析API
"""

from . import reconstruction, model_management, upload, websocket, auth, online_training, reconstruction_history, medical_analysis 