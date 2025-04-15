from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
from typing import List
import threading
import time
from datetime import datetime
from pydantic import BaseModel
import torch
import logging

# 创建路由
router = APIRouter()

# 存储训练任务状态的字典
training_tasks = {}

# 确保模型保存目录存在
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

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
        self.model = None
        self.model_path = None  # 添加模型保存路径字段

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
            'log_message': self.log_messages[-1] if self.log_messages else None,
            'model_path': self.model_path  # 添加模型路径到返回数据中
        }

def train_model(task_id: str, training_data_path: str, epochs: int, batch_size: int):
    """模型训练过程"""
    task = training_tasks[task_id]
    
    try:
        logger.info(f"开始训练任务 {task_id}")
        
        # 创建一个简单的模型用于演示
        model = torch.nn.Sequential(
            torch.nn.Linear(784, 256),
            torch.nn.ReLU(),
            torch.nn.Linear(256, 784)
        )
        
        # 确保模型保存目录存在
        os.makedirs(MODELS_DIR, exist_ok=True)
        
        total_epochs = epochs
        for epoch in range(total_epochs):
            try:
                # 更新任务状态
                task.current_epoch = epoch + 1
                task.progress = ((epoch + 1) / total_epochs) * 100
                task.current_loss = 0.5 / (epoch + 1)  # 模拟损失值下降
                task.add_log(f"轮次 {epoch + 1}/{total_epochs} 完成，损失值: {task.current_loss:.4f}")
                
                logger.info(f"任务 {task_id} - 轮次 {epoch + 1}/{total_epochs}, 损失值: {task.current_loss:.4f}")
                
                # 模拟训练时间
                time.sleep(1)
            except Exception as e:
                logger.error(f"训练轮次 {epoch + 1} 出错: {str(e)}")
                continue
        
        # 训练完成后保存模型
        try:
            model_filename = f"model_{task_id}.pt"
            model_path = os.path.join(MODELS_DIR, model_filename)
            
            # 保存模型和训练信息
            torch.save({
                'model_state_dict': model.state_dict(),
                'task_id': task_id,
                'training_info': {
                    'epochs': epochs,
                    'batch_size': batch_size,
                    'final_loss': task.current_loss,
                    'training_date': datetime.now().isoformat()
                }
            }, model_path)
            
            # 更新任务状态
            task.status = 'completed'
            task.progress = 100
            task.model_path = model_path
            task.add_log(f"训练完成！模型已保存至: {model_path}")
            logger.info(f"训练任务 {task_id} 完成")
            
        except Exception as e:
            logger.error(f"保存模型时出错: {str(e)}")
            raise
        
    except Exception as e:
        logger.error(f"训练任务 {task_id} 失败: {str(e)}")
        task.status = 'failed'
        task.error = str(e)
        task.add_log(f"训练失败：{str(e)}")
        raise  # 重新抛出异常以便调试

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
        task = TrainingTask(task_id, f"model_{task_id}")
        training_tasks[task_id] = task
        task.status = 'running'
        task.add_log('开始训练...')
        
        # 在后台线程中启动训练
        thread = threading.Thread(
            target=train_model,
            args=(task_id, data_dir, epochs, batch_size),
            daemon=False  # 确保线程不会随主线程退出而终止
        )
        thread.start()
        
        return {
            'task_id': task_id,
            'message': '训练任务已启动'
        }
        
    except Exception as e:
        logger.error(f"启动训练任务时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progress/{task_id}")
async def get_training_progress(task_id: str):
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail='任务不存在')
        
    return training_tasks[task_id].to_dict() 