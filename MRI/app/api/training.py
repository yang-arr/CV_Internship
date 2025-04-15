from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
from typing import List
import threading
import time
from datetime import datetime
from pydantic import BaseModel

# 创建路由
router = APIRouter()

# 存储训练任务状态的字典
training_tasks = {}

class TrainingTask:
    def __init__(self, task_id: str, model_name: str):
        self.task_id = task_id
        self.model_name = model_name
        self.status = 'pending'
        self.progress = 0
        self.current_epoch = 0
        self.current_loss = 0.0
        self.error = None
        self.log_messages = []

    def add_log(self, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_messages.append(f'[{timestamp}] {message}')

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'status': self.status,
            'progress': self.progress,
            'current_epoch': self.current_epoch,
            'current_loss': self.current_loss,
            'error': self.error,
            'log_message': self.log_messages[-1] if self.log_messages else None
        }

def train_model(task_id: str, training_data_path: str, epochs: int, batch_size: int):
    """模拟模型训练过程"""
    task = training_tasks[task_id]
    
    try:
        total_epochs = epochs
        for epoch in range(total_epochs):
            # 更新任务状态
            task['current_epoch'] = epoch + 1
            task['progress'] = ((epoch + 1) / total_epochs) * 100
            task['loss'] = 0.5 / (epoch + 1)  # 模拟损失值下降
            task['logs'].append(f"轮次 {epoch + 1}/{total_epochs} 完成，损失值: {task['loss']:.4f}")
            
            # 模拟训练时间
            time.sleep(2)
        
        task['status'] = 'completed'
        task['progress'] = 100
        task['logs'].append("训练完成！")
        
    except Exception as e:
        task['status'] = 'failed'
        task['error'] = str(e)
        task['logs'].append(f"训练失败：{str(e)}")

@router.post("/start")
async def start_training(
    training_data: List[UploadFile] = File(...),
    epochs: int = Form(10),
    batch_size: int = Form(32)
):
    try:
        # 创建临时目录存储训练数据
        task_id = str(uuid.uuid4())
        data_dir = os.path.join('temp', task_id)
        os.makedirs(data_dir, exist_ok=True)
        
        # 保存上传的文件
        file_paths = []
        for file in training_data:
            file_path = os.path.join(data_dir, file.filename)
            with open(file_path, 'wb') as buffer:
                content = await file.read()
                buffer.write(content)
            file_paths.append(file_path)
        
        # 创建训练任务
        training_tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'current_epoch': 0,
            'loss': None,
            'logs': ['开始训练...'],
            'error': None
        }
        
        # 在后台线程中启动训练
        thread = threading.Thread(
            target=train_model,
            args=(task_id, data_dir, epochs, batch_size)
        )
        thread.start()
        
        return {
            'task_id': task_id,
            'message': '训练任务已启动'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progress/{task_id}")
async def get_training_progress(task_id: str):
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail='任务不存在')
        
    return training_tasks[task_id] 