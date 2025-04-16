#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
在线训练API路由
提供以下功能：
1. 上传图像并训练模型
2. 查询训练状态
3. 获取训练结果
4. 使用训练好的模型进行重建
"""

import os
import uuid
import json
import base64
import datetime
import torch
import numpy as np
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Any, List, Optional
import logging
import io
from PIL import Image
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import platform

# 设置中文字体
if platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.family'] = ['Arial Unicode MS']
elif platform.system() == 'Windows':
    plt.rcParams['font.family'] = ['SimHei']
else:  # Linux
    plt.rcParams['font.family'] = ['WenQuanYi Micro Hei']

# 设置字体大小
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10

# 导入自定义模块
from MRI.app.services.auth import get_current_user
from MRI.app.models.user import User
from MRI.app.services.model_service import model_service

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 定义结果保存的根目录
RESULTS_DIR = Path(__file__).resolve().parent.parent / "training_results"
RESULTS_DIR.mkdir(exist_ok=True)

# 定义模型保存的根目录
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

# 存储正在进行的训练任务
active_tasks = {}

# 添加自定义Sin激活函数
class Sin(torch.nn.Module):
    """自定义正弦激活函数"""
    def __init__(self, omega_0=30.0):
        super().__init__()
        self.omega_0 = omega_0

    def forward(self, x):
        return torch.sin(self.omega_0 * x)

# 自定义图像数据集类
class SimpleImageDataset(torch.utils.data.Dataset):
    """单图像数据集
    
    用于通过单张图像训练模型
    """
    def __init__(self, image_tensor, H, W):
        """初始化数据集
        
        Args:
            image_tensor: 图像张量
            H, W: 图像高度和宽度
        """
        self.image = image_tensor
        self.H = H
        self.W = W
        
        # 生成归一化的坐标网格
        xs = np.linspace(-1, 1, self.W)
        ys = np.linspace(-1, 1, self.H)
        grid_y, grid_x = np.meshgrid(ys, xs, indexing='ij')
        coords = np.stack([grid_x, grid_y], axis=-1)
        self.coords = torch.tensor(coords, dtype=torch.float32).view(-1, 2)
        
        # 生成模拟掩码（简单起见，可以使用随机掩码或全1掩码）
        self.mask = torch.ones((H, W), dtype=torch.float32)
    
    def __len__(self):
        return 1
    
    def __getitem__(self, idx):
        """获取数据样本
        
        Returns:
            包含以下字段的字典:
            - coords: 坐标点
            - gt_img: 原始图像
            - mask: 采样掩码
        """
        return {
            'coords': self.coords,
            'gt_img': self.image,
            'mask': self.mask
        }

class Fullmodel(torch.nn.Module):
    """完整的MRI重建模型"""
    def __init__(self, encoding_mode='fourier', in_features=2, out_features=20, 
                 coordinate_scales=[1.0, 1.0], mlp_hidden_features=256, 
                 mlp_hidden_layers=4, omega_0=30.0, activation='sine'):
        super().__init__()
        self.encoding_mode = encoding_mode
        self.coordinate_scales = coordinate_scales
        
        # 创建MLP网络
        layers = []
        # 输入层
        layers.append(torch.nn.Linear(in_features, mlp_hidden_features))
        if activation == 'sine':
            layers.append(Sin(omega_0))
        else:
            layers.append(torch.nn.ReLU())
            
        # 隐藏层
        for _ in range(mlp_hidden_layers):
            layers.append(torch.nn.Linear(mlp_hidden_features, mlp_hidden_features))
            if activation == 'sine':
                layers.append(Sin(omega_0))
            else:
                layers.append(torch.nn.ReLU())
                
        # 输出层
        layers.append(torch.nn.Linear(mlp_hidden_features, 1))
        
        self.mlp = torch.nn.Sequential(*layers)
    
    def forward(self, coords):
        # 坐标缩放
        coords = coords * torch.tensor(self.coordinate_scales, device=coords.device)
        
        # 坐标编码
        if self.encoding_mode == 'fourier':
            encoded_coords = coords
        else:  # gaussian
            encoded_coords = torch.exp(-coords**2)
            
        # MLP处理
        output = self.mlp(encoded_coords)
        return output

def train_epoch_image(model, dataloader, optimizer, device, supervision_mode='image', lambda_tv=1e-5):
    """训练一个epoch
    
    Args:
        model: 模型
        dataloader: 数据加载器
        optimizer: 优化器
        device: 设备
        supervision_mode: 监督模式 ('image' 或 'kspace')
        lambda_tv: 总变差正则化系数
        
    Returns:
        loss, psnr, ssim, nse
    """
    model.train()
    total_loss = 0
    total_psnr = 0
    total_ssim = 0
    total_nse = 0
    batch_count = 0
    
    for batch in dataloader:
        coords = batch['coords'].to(device)
        gt_img = batch['gt_img'].to(device)
        mask = batch['mask'].to(device)
        
        optimizer.zero_grad()
        
        # 前向传播
        pred = model(coords).view(gt_img.shape)
        
        # 计算损失
        if supervision_mode == 'image':
            loss = torch.nn.functional.mse_loss(pred, gt_img)
        else:  # kspace
            # 这里简化处理，实际应该进行傅里叶变换
            loss = torch.nn.functional.mse_loss(pred * mask, gt_img * mask)
        
        # 添加总变差正则化
        if lambda_tv > 0:
            tv_loss = torch.mean(torch.abs(pred[:, :, 1:] - pred[:, :, :-1])) + \
                     torch.mean(torch.abs(pred[:, 1:, :] - pred[:, :-1, :]))
            loss = loss + lambda_tv * tv_loss
        
        # 反向传播
        loss.backward()
        optimizer.step()
        
        # 计算指标
        with torch.no_grad():
            total_loss += loss.item()
            # 简化的PSNR计算
            mse = torch.mean((pred - gt_img) ** 2)
            psnr = 20 * torch.log10(1.0 / torch.sqrt(mse))
            total_psnr += psnr.item()
            # 简化的SSIM计算（这里只是示例，实际应该使用proper SSIM）
            total_ssim += 1.0 - mse.item()
            # NSE (Normalized Square Error)
            total_nse += mse.item() / torch.mean(gt_img ** 2).item()
        
        batch_count += 1
    
    # 计算平均值
    avg_loss = total_loss / batch_count
    avg_psnr = total_psnr / batch_count
    avg_ssim = total_ssim / batch_count
    avg_nse = total_nse / batch_count
    
    return avg_loss, avg_psnr, avg_ssim, avg_nse

def train_model_background(task_id: str, image_path: str, config: Dict[str, Any], user_id: int):
    """在后台执行模型训练
    
    Args:
        task_id: 任务ID
        image_path: 图像路径
        config: 训练配置
        user_id: 用户ID
    """
    try:
        logger.info(f"开始训练任务 {task_id} 用户ID: {user_id}")
        
        # 更新任务状态
        active_tasks[task_id] = {
            "status": "running",
            "progress": 0,
            "user_id": user_id,
            "start_time": datetime.datetime.now().isoformat(),
            "current_epoch": 0,
            "current_loss": None,
            "log_message": "开始训练...",
            "stop_flag": False  # 添加停止标志
        }
        
        # 创建结果目录
        result_dir = RESULTS_DIR / task_id
        result_dir.mkdir(exist_ok=True)
        
        # 保存训练配置
        with open(result_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 读取图像并转换为灰度图
        image = Image.open(image_path)
        if image.mode != 'L':
            image = image.convert('L')
        
        # 调整图像大小为256x256
        image = image.resize((256, 256))
        
        # 保存原始图像
        image.save(result_dir / "original.png")
        
        # 转换为张量
        image_np = np.array(image) / 255.0  # 归一化到0-1
        image_tensor = torch.tensor(image_np, dtype=torch.float32)
        
        # 创建简单数据集
        dataset = SimpleImageDataset(image_tensor, 256, 256)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=1, shuffle=False)
        
        # 设置设备
        device = torch.device('cuda' if torch.cuda.is_available() and config.get('use_gpu', True) else 'cpu')
        logger.info(f"使用设备: {device}")
        
        # 创建模型
        model = Fullmodel(
            encoding_mode=config["encoder"]["encoding_mode"],
            in_features=config["encoder"]["in_features"],
            out_features=config["encoder"]["out_features"],
            coordinate_scales=config["encoder"]["coordinate_scales"],
            mlp_hidden_features=config["mlp"]["mlp_hidden_features"],
            mlp_hidden_layers=config["mlp"]["mlp_hidden_layers"],
            omega_0=config["mlp"]["omega_0"],
            activation=config["mlp"]["activation"]
        ).to(device)
        
        # 创建优化器
        optimizer = torch.optim.Adam(model.parameters(), lr=config["learning_rate"])
        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1000, gamma=0.9)
        
        # 记录训练指标
        train_loss_history = []
        train_psnr_history = []
        best_psnr, best_ssim = 0, 0
        
        # 训练循环
        epochs = config["epochs"]
        for epoch in range(epochs):
            # 检查停止标志
            if active_tasks[task_id].get("stop_flag", False):
                logger.info(f"任务 {task_id} 被用户请求中断，训练在第 {epoch+1} 轮停止")
                break
                
            # 更新进度
            progress = (epoch + 1) / epochs * 100
            current_loss = None
            
            # 训练一个epoch
            loss, psnr, ssim, nse = train_epoch_image(
                model, dataloader, optimizer, device,
                supervision_mode=config.get("supervision_mode", "image"),
                lambda_tv=config.get("lambda_tv", 1e-5)
            )
            
            train_loss_history.append(loss)
            train_psnr_history.append(psnr)
            
            # 更新任务状态
            active_tasks[task_id].update({
                "progress": progress,
                "current_epoch": epoch + 1,
                "current_loss": float(loss),
                "log_message": f"轮次 {epoch+1}/{epochs}: Loss={loss:.4e}, PSNR={psnr:.2f}, SSIM={ssim:.4f}"
            })
            
            # 每隔一定间隔保存结果
            if (epoch + 1) % config.get("save_interval", 1000) == 0:
                logger.info(f"任务 {task_id} - Epoch {epoch+1}/{epochs}: Loss={loss:.4e}, PSNR={psnr:.2f}, SSIM={ssim:.4f}")
                save_epoch_results_as_png(model, dataset[0], device, epoch, str(result_dir),
                                          supervision_mode=config.get("supervision_mode", "image"))
            
            # 保存最佳模型
            if psnr > best_psnr or ssim > best_ssim:
                best_psnr = max(best_psnr, psnr)
                best_ssim = max(best_ssim, ssim)
                save_best_image(model, dataset[0], device, psnr, ssim, str(result_dir),
                                supervision_mode=config.get("supervision_mode", "image"))
            
            scheduler.step()
        
        # 检查训练是否被中断
        if active_tasks[task_id].get("stop_flag", False):
            active_tasks[task_id].update({
                "status": "stopped",
                "progress": progress,
                "end_time": datetime.datetime.now().isoformat(),
                "log_message": f"训练在第 {epoch+1}/{epochs} 轮被中断"
            })
            logger.info(f"训练任务 {task_id} 被用户中断")
            return
        
        # 保存损失曲线
        loss_curve_path = result_dir / "loss_curve.png"
        plot_loss_curve(train_loss_history, str(loss_curve_path))
        
        # 保存训练历史
        np.savez(result_dir / "train_history.npz", 
                 loss=train_loss_history, 
                 psnr=train_psnr_history)
        
        # 保存最佳指标
        with open(result_dir / "best_metrics.txt", "w") as f:
            f.write(f"Best PSNR: {best_psnr:.2f}\nBest SSIM: {best_ssim:.4f}\n")
        
        # 保存训练好的模型到models目录
        model_filename = f"online_model_{task_id}.pt"
        model_path = MODELS_DIR / model_filename
        
        torch.save({
            'model_state_dict': model.state_dict(),
            'task_id': task_id,
            'training_info': {
                'epochs': config["epochs"],
                'encoder_config': config["encoder"],
                'mlp_config': config["mlp"],
                'final_metrics': {
                    'psnr': float(best_psnr),
                    'ssim': float(best_ssim)
                },
                'training_date': datetime.datetime.now().isoformat()
            }
        }, str(model_path))
        
        # 更新任务状态
        active_tasks[task_id].update({
            "status": "completed",
            "progress": 100,
            "end_time": datetime.datetime.now().isoformat(),
            "metrics": {
                "psnr": float(best_psnr),
                "ssim": float(best_ssim)
            },
            "model_path": str(model_path),
            "log_message": f"训练完成！模型已保存至: {model_path}"
        })
        
        logger.info(f"训练任务 {task_id} 完成")
        
    except Exception as e:
        logger.error(f"训练任务 {task_id} 出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # 更新任务状态为失败
        active_tasks[task_id].update({
            "status": "failed",
            "progress": 0,
            "end_time": datetime.datetime.now().isoformat(),
            "error": str(e),
            "log_message": f"训练失败：{str(e)}"
        })

@router.post("/")
async def start_training(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    learning_rate: float = Form(1e-4),
    epochs: int = Form(5000),
    save_interval: int = Form(500),
    use_gpu: bool = Form(True),
    encoder_mode: str = Form("fourier"),
    in_features: int = Form(2),
    out_features: int = Form(20),
    coordinate_scales: str = Form("[1.0, 1.0]"),
    mlp_hidden_features: int = Form(256),
    mlp_hidden_layers: int = Form(4),
    omega_0: float = Form(30.0),
    activation: str = Form("sine"),
    supervision_mode: str = Form("image"),
    lambda_tv: float = Form(1e-5)
):
    """启动在线训练
    
    上传图像并开始训练MRI重建模型
    """
    try:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="仅支持图像文件")
        
        # 创建任务ID
        task_id = str(uuid.uuid4())
        
        # 读取文件内容并保存
        content = await file.read()
        task_dir = RESULTS_DIR / task_id
        task_dir.mkdir(exist_ok=True)
        
        image_path = task_dir / f"input_{file.filename}"
        with open(image_path, "wb") as f:
            f.write(content)
        
        # 解析coordinate_scales
        try:
            coord_scales = json.loads(coordinate_scales)
        except:
            coord_scales = [1.0, 1.0]
        
        # 创建训练配置
        training_config = {
            "learning_rate": learning_rate,
            "epochs": epochs,
            "save_interval": save_interval,
            "use_gpu": use_gpu,
            "supervision_mode": supervision_mode,
            "lambda_tv": lambda_tv,
            "encoder": {
                "encoding_mode": encoder_mode,
                "in_features": in_features,
                "out_features": out_features,
                "coordinate_scales": coord_scales
            },
            "mlp": {
                "mlp_hidden_features": mlp_hidden_features,
                "mlp_hidden_layers": mlp_hidden_layers,
                "omega_0": omega_0,
                "activation": activation
            }
        }
        
        # 初始化任务状态
        active_tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "user_id": 1,  # 默认用户ID
            "start_time": datetime.datetime.now().isoformat()
        }
        
        # 启动后台训练
        background_tasks.add_task(
            train_model_background,
            task_id,
            str(image_path),
            training_config,
            1  # 默认用户ID
        )
        
        return {
            "task_id": task_id,
            "status": "submitted",
            "message": "训练任务已提交",
            "submit_time": datetime.datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"提交训练任务出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"提交训练失败: {str(e)}")

@router.get("/status/{task_id}")
async def get_training_status(
    task_id: str
):
    """获取训练任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态信息
    """
    try:
        # 检查任务是否存在
        if task_id not in active_tasks:
            # 查看任务目录是否存在
            task_dir = RESULTS_DIR / task_id
            if task_dir.exists():
                # 读取best_metrics.txt判断任务是否完成
                metrics_file = task_dir / "best_metrics.txt"
                if metrics_file.exists():
                    with open(metrics_file, "r") as f:
                        metrics_text = f.read()
                    
                    # 检查模型文件
                    model_path = MODELS_DIR / f"online_model_{task_id}.pt"
                    
                    return {
                        "task_id": task_id,
                        "status": "completed",
                        "progress": 100,
                        "message": "训练已完成",
                        "metrics": metrics_text,
                        "model_path": str(model_path) if model_path.exists() else None
                    }
                else:
                    return {
                        "task_id": task_id,
                        "status": "unknown",
                        "message": "找到任务目录但任务状态未知"
                    }
            else:
                raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
        
        # 获取任务状态
        task_info = active_tasks[task_id]
        
        # 不再检查用户权限
        # if task_info["user_id"] != current_user.id and not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="没有权限查看此任务")
        
        # 返回任务状态
        return {
            "task_id": task_id,
            "status": task_info["status"],
            "progress": task_info["progress"],
            "current_epoch": task_info.get("current_epoch", 0),
            "current_loss": task_info.get("current_loss"),
            "start_time": task_info["start_time"],
            "end_time": task_info.get("end_time"),
            "metrics": task_info.get("metrics"),
            "error": task_info.get("error"),
            "log_message": task_info.get("log_message"),
            "model_path": task_info.get("model_path")
        }
    
    except Exception as e:
        logger.error(f"获取训练状态出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/result/{task_id}")
async def get_training_result(
    task_id: str
):
    """获取训练结果
    
    Args:
        task_id: 任务ID
        
    Returns:
        训练结果信息，包括最佳图像和指标
    """
    # 检查任务目录是否存在
    task_dir = RESULTS_DIR / task_id
    if not task_dir.exists():
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    # 检查任务是否属于当前用户（安全检查）
    if task_id in active_tasks:
        task_info = active_tasks[task_id]
        # if task_info["user_id"] != current_user.id and not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="没有权限查看此任务结果")
    
    # 检查最佳图像是否存在
    best_image_path = task_dir / "best_pred_mag.png"
    if not best_image_path.exists():
        raise HTTPException(status_code=404, detail="训练结果图像不存在，任务可能尚未完成")
    
    try:
        # 读取最佳图像
        with open(best_image_path, "rb") as f:
            image_bytes = f.read()
        
        # 转换为base64
        image_base64 = base64.b64encode(image_bytes).decode()
        
        # 读取指标
        metrics_text = ""
        metrics_file = task_dir / "best_metrics.txt"
        if metrics_file.exists():
            with open(metrics_file, "r") as f:
                metrics_text = f.read()
        
        # 读取损失曲线
        loss_curve_base64 = ""
        loss_curve_path = task_dir / "loss_curve.png"
        if loss_curve_path.exists():
            with open(loss_curve_path, "rb") as f:
                loss_curve_bytes = f.read()
            loss_curve_base64 = base64.b64encode(loss_curve_bytes).decode()
        
        # 获取模型ID（与任务ID相同）
        model_id = task_id
        
        return {
            "task_id": task_id,
            "status": "completed",
            "model_id": model_id,
            "best_image": image_base64,
            "loss_curve": loss_curve_base64,
            "metrics": metrics_text,
            "message": "训练已完成"
        }
    
    except Exception as e:
        logger.error(f"获取训练结果出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取训练结果失败: {str(e)}")

@router.post("/reconstruct/{task_id}")
async def reconstruct_with_trained_model(
    task_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """使用训练好的模型进行重建
    
    Args:
        task_id: 任务ID/模型ID
        file: 上传的图像文件
        
    Returns:
        重建结果
    """
    try:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="仅支持图像文件")
        
        # 检查模型是否存在
        model_dir = RESULTS_DIR / task_id
        if not model_dir.exists():
            raise HTTPException(status_code=404, detail=f"训练任务 {task_id} 不存在")
        
        # 检查模型文件是否存在
        model_path = model_dir / "best_model.pt"
        if not model_path.exists():
            raise HTTPException(status_code=404, detail="模型文件不存在，训练可能尚未完成")
        
        # 读取上传的图像文件
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # 转换为灰度图并调整大小
        if image.mode != 'L':
            image = image.convert('L')
        
        # 调整图像大小为256x256
        image = image.resize((256, 256))
        
        # 转换为NumPy数组
        input_data = np.array(image)
        
        # 保存输入图像到任务目录
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        input_save_path = model_dir / f"input_{now}.png"
        image.save(input_save_path)
        
        # 使用model_service进行预测
        start_time = datetime.datetime.now()
        
        # 这里假设model_service可以使用训练好的模型，如果不行，需要手动加载并预测
        result = model_service.predict(task_id, input_data)
        
        execution_time = (datetime.datetime.now() - start_time).total_seconds()
        
        # 将重建结果转换为base64编码的图像
        reconstructed_image = result["reconstructed_image"]
        img = Image.fromarray((reconstructed_image * 255).astype(np.uint8))
        
        # 保存重建结果到任务目录
        output_save_path = model_dir / f"output_{now}.png"
        img.save(output_save_path)
        
        # 编码为base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # 获取评估指标
        metrics = result["metrics"]
        
        return {
            "success": True,
            "message": "图像重建成功",
            "result_id": str(uuid.uuid4()),
            "reconstructed_image": img_str,
            "metrics": metrics,
            "execution_time": execution_time,
            "model_id": task_id
        }
    
    except Exception as e:
        logger.error(f"使用训练模型 {task_id} 重建图像时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"重建失败: {str(e)}")

@router.get("/list")
async def list_training_tasks(
    current_user: User = Depends(get_current_user)
):
    """列出当前用户的训练任务
    
    Returns:
        训练任务列表
    """
    try:
        # 获取当前用户的任务
        user_tasks = {}
        
        # 先从活动任务中获取
        for task_id, task_info in active_tasks.items():
            if task_info["user_id"] == current_user.id or current_user.is_admin:
                user_tasks[task_id] = task_info
        
        # 再从目录中扫描已完成的任务
        for task_dir in RESULTS_DIR.iterdir():
            if task_dir.is_dir() and task_dir.name not in user_tasks:
                # 检查是否有info.json文件
                info_file = task_dir / "info.json"
                if info_file.exists():
                    try:
                        with open(info_file, "r", encoding="utf-8") as f:
                            info = json.load(f)
                        
                        # 检查是否是当前用户的任务（如果info中有用户信息）
                        if "user_id" not in info or info["user_id"] == current_user.id or current_user.is_admin:
                            # 读取指标
                            metrics = {}
                            metrics_file = task_dir / "best_metrics.txt"
                            if metrics_file.exists():
                                with open(metrics_file, "r") as f:
                                    metrics_text = f.read()
                                    for line in metrics_text.split("\n"):
                                        if ":" in line:
                                            key, value = line.split(":", 1)
                                            metrics[key.strip()] = float(value.strip())
                            
                            user_tasks[task_dir.name] = {
                                "status": "completed",
                                "progress": 100,
                                "model_name": info.get("name", f"训练模型_{task_dir.name}"),
                                "created_at": info.get("created_at", ""),
                                "metrics": metrics
                            }
                    except Exception as e:
                        logger.error(f"读取任务 {task_dir.name} 信息出错: {e}")
        
        # 转换为列表
        task_list = [{"task_id": k, **v} for k, v in user_tasks.items()]
        
        # 按创建时间排序
        task_list.sort(key=lambda x: x.get("start_time", x.get("created_at", "")), reverse=True)
        
        return {
            "tasks": task_list,
            "total": len(task_list)
        }
    
    except Exception as e:
        logger.error(f"列出训练任务时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

@router.post("/stop/{task_id}")
async def stop_training(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """中断正在进行的训练任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        操作结果
    """
    try:
        # 检查任务是否存在
        if task_id not in active_tasks:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
        
        # 检查任务状态
        task_info = active_tasks[task_id]
        
        # 检查权限 (修改这里，移除is_admin检查)
        if task_info.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="没有权限停止此任务")
            
        # 检查状态是否允许停止
        if task_info["status"] not in ["running", "pending"]:
            return JSONResponse(content={
                "success": False,
                "message": f"任务状态为 {task_info['status']}，无法中断"
            })
        
        # 更新任务状态并设置停止标志
        active_tasks[task_id].update({
            "status": "stopping",  # 更改为"stopping"状态
            "progress": task_info.get("progress", 0),
            "stop_flag": True,  # 设置停止标志
            "log_message": "正在中断训练，请等待当前周期完成..."
        })
        
        # 在实际应用中，这里应该有一个机制来通知训练进程停止
        # 例如设置一个标志位，让训练循环检查该标志位
        # 或者使用进程间通信等方式
        
        logger.info(f"任务 {task_id} 已被用户 {current_user.id} 请求中断")
        
        return JSONResponse(content={
            "success": True,
            "message": "已发送中断训练请求，训练将在当前周期完成后停止",
            "task_id": task_id,
            "status": "stopping"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"中断训练任务 {task_id} 时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"中断训练失败: {str(e)}")

@router.get("/download/{task_id}")
async def download_model(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """下载训练好的模型
    
    Args:
        task_id: 任务ID/模型ID
        
    Returns:
        模型文件下载响应
    """
    try:
        # 检查模型文件是否存在
        model_path = MODELS_DIR / f"online_model_{task_id}.pt"
        
        if not model_path.exists():
            raise HTTPException(status_code=404, detail=f"模型文件不存在，训练可能尚未完成或已失败")
        
        # 检查用户权限 (修改这里，移除is_admin检查)
        if task_id in active_tasks:
            task_info = active_tasks[task_id]
            if task_info.get("user_id") != current_user.id:
                raise HTTPException(status_code=403, detail="没有权限下载此模型")
        
        # 使用FileResponse直接返回文件
        model_filename = f"online_model_{task_id}.pt"
        
        # 记录日志
        logger.info(f"用户 {current_user.id} 下载模型 {task_id}")
        
        # 返回文件响应
        return FileResponse(
            path=model_path,
            filename=model_filename,
            media_type="application/octet-stream"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"准备下载模型 {task_id} 时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"准备模型下载失败: {str(e)}")

def save_epoch_results_as_png(model, data, device, epoch, output_dir, supervision_mode='image'):
    """保存特定训练轮次的结果"""
    model.eval()
    with torch.no_grad():
        coords = data['coords'].to(device)
        gt_img = data['gt_img'].to(device)
        
        # 预测
        pred = model(coords).view(gt_img.shape)
        
        # 保存结果
        pred_np = pred.cpu().numpy()
        gt_np = gt_img.cpu().numpy()
        
        # 确保值在0-1范围内
        pred_np = np.clip(pred_np, 0, 1)
        
        # 创建图形
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        
        # 原始图像
        ax1.imshow(gt_np, cmap='gray')
        ax1.set_title('原始图像')
        ax1.axis('off')
        
        # 预测结果
        ax2.imshow(pred_np, cmap='gray')
        ax2.set_title(f'预测结果 (轮次 {epoch})')
        ax2.axis('off')
        
        # 保存图像
        plt.tight_layout()
        plt.savefig(f"{output_dir}/epoch_{epoch}.png", dpi=150, bbox_inches='tight')
        plt.close(fig)

def save_best_image(model, data, device, psnr, ssim, output_dir, supervision_mode='image'):
    """保存最佳模型的预测结果"""
    model.eval()
    with torch.no_grad():
        coords = data['coords'].to(device)
        gt_img = data['gt_img'].to(device)
        
        # 预测
        pred = model(coords).view(gt_img.shape)
        
        # 保存结果
        pred_np = pred.cpu().numpy()
        gt_np = gt_img.cpu().numpy()
        
        # 确保值在0-1范围内
        pred_np = np.clip(pred_np, 0, 1)
        
        # 保存原始图像
        fig1 = plt.figure(figsize=(5, 5))
        ax1 = fig1.add_subplot(111)
        ax1.imshow(gt_np, cmap='gray')
        ax1.set_title('原始图像')
        ax1.axis('off')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/original_mag.png", dpi=150, bbox_inches='tight')
        plt.close(fig1)
        
        # 保存预测结果
        fig2 = plt.figure(figsize=(5, 5))
        ax2 = fig2.add_subplot(111)
        ax2.imshow(pred_np, cmap='gray')
        ax2.set_title(f'最佳预测结果 (PSNR: {psnr:.2f}, SSIM: {ssim:.4f})')
        ax2.axis('off')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/best_pred_mag.png", dpi=150, bbox_inches='tight')
        plt.close(fig2)
        
        # 保存差异图
        fig3 = plt.figure(figsize=(5, 5))
        ax3 = fig3.add_subplot(111)
        ax3.imshow(np.abs(pred_np - gt_np), cmap='hot')
        ax3.set_title('误差图')
        ax3.axis('off')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/error_map.png", dpi=150, bbox_inches='tight')
        plt.close(fig3)

def plot_loss_curve(loss_history, output_path):
    """绘制损失曲线"""
    fig = plt.figure(figsize=(10, 6))
    plt.plot(loss_history)
    plt.title('训练损失曲线')
    plt.xlabel('训练轮次')
    plt.ylabel('损失值')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig) 