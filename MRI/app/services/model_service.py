#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型服务层
负责模型的加载、预测和结果处理
"""

import os
import json
import torch
import numpy as np
from pathlib import Path
import sys
import logging
from typing import Dict, List, Any, Optional

# 添加项目根目录到系统路径，确保能导入到原有的模型模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入原有的模型和工具函数
from MRI.LoadModel.model import Fullmodel

# 为了兼容性，将 MRI.LoadModel 模块设置为可通过 'model' 名称访问
import sys
import MRI.LoadModel.model
sys.modules['model'] = MRI.LoadModel.model

# 自定义函数，用于从模型输出生成图像
def get_image_from_prediction(prediction):
    """
    从模型预测结果生成图像
    
    Args:
        prediction: 模型输出的预测结果，包含实部和虚部
        
    Returns:
        numpy.ndarray: 生成的图像
    """
    # 检查预测结果的形状
    if len(prediction.shape) == 2:
        # 假设是[N, 2]的形状，分别表示实部和虚部
        n_points = prediction.shape[0]
        size = int(np.sqrt(n_points))
        
        # 重塑为图像形状
        pred_complex = prediction[:, 0] + 1j * prediction[:, 1]
        pred_image = np.abs(pred_complex.reshape(size, size))
        
        # 归一化到[0,1]范围
        normalized_image = (pred_image - pred_image.min()) / (pred_image.max() - pred_image.min() + 1e-8)
        
        return normalized_image
    else:
        # 其他情况，尝试取预测结果的幅值
        if hasattr(prediction, 'abs'):  # 如果是复数张量
            return np.abs(prediction)
        else:
            return prediction  # 直接返回结果

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelService:
    """
    模型服务类
    负责模型的加载、预测和结果处理
    """
    
    def __init__(self):
        """初始化模型服务"""
        # 设置模型目录
        self.models_dir = Path(__file__).resolve().parent.parent / "models"
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.loaded_models = {}  # 缓存已加载的模型
        
        logger.info(f"ModelService initialized. Using device: {self.device}")
        logger.info(f"Models directory: {self.models_dir}")
        
        # 默认模型配置
        self.default_model_config = {
            "name": "默认MRI重建模型",
            "description": "基于隐式神经表示的MRI重建模型",
            "id": "default_model",
            "created_at": "2023-04-06T13:45:00Z",
            "parameters": {
                "input_size": 256,
                "output_size": 256,
                "model_type": "SIREN"
            },
            "metrics": {
                "psnr": 32.5,
                "ssim": 0.9450,
                "nse": 0.9
            },
            "config": {
                "encoder": {
                    "encoding_mode": "fourier",
                    "in_features": 2,
                    "out_features": 20,
                    "coordinate_scales": [1.0, 1.0]
                },
                "mlp": {
                    "mlp_hidden_features": 256,
                    "mlp_hidden_layers": 4,
                    "omega_0": 30,
                    "activation": "sine"
                }
            }
        }

    def get_models_list(self) -> List[Dict]:
        """
        获取所有模型信息列表
        
        Returns:
            List[Dict]: 模型信息列表（只包含名称、描述和创建时间）
        """
        models_list = []
        # 列出 models_dir 中的所有子目录作为模型
        if os.path.exists(self.models_dir):
            model_dirs = [d for d in os.scandir(self.models_dir) if d.is_dir() and not d.name.startswith('__')]
            
            logger.info(f"Scanning model directories in {self.models_dir}")
            for model_dir in model_dirs:
                model_id = model_dir.name
                logger.info(f"Found model directory: {model_id}")
                model_info = self.get_model_info(model_id)
                
                if model_info:
                    logger.info(f"Adding model to list: {model_id}")
                    models_list.append(model_info)
                else:
                    # 如果没有找到配置文件，创建一个基于默认配置的模型信息
                    logger.warning(f"No info.json found for model: {model_id}, using fallback")
                    basic_info = self._filter_model_info_for_api(
                        self._ensure_complete_model_info({
                            "name": model_id,
                            "description": f"模型位于 {model_dir.path}",
                            "id": model_id,
                            "created_at": "未知"
                        }, model_id)
                    )
                    models_list.append(basic_info)
            
            logger.info(f"Found {len(models_list)} models in {self.models_dir}")
        else:
            logger.warning(f"Models directory not found: {self.models_dir}")
            # 如果模型目录不存在，至少返回默认模型
            models_list.append(self._filter_model_info_for_api(self.default_model_config))
            
        return models_list
    
    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """
        获取指定模型的信息
        
        Args:
            model_id: 模型ID
            
        Returns:
            Dict: 模型信息（包含名称、描述和创建时间）
        """
        # 检查模型目录中是否存在info.json文件
        model_info_path = os.path.join(self.models_dir, model_id, "info.json")
        logger.info(f"Looking for model info at: {model_info_path}")
        
        if os.path.exists(model_info_path):
            try:
                with open(model_info_path, 'r', encoding='utf-8') as f:
                    model_info = json.load(f)
                
                logger.info(f"Successfully loaded model info for: {model_id}")
                
                # 确保包含所有必要字段，如果缺少则补充默认值
                model_info = self._ensure_complete_model_info(model_info, model_id)
                
                # 为API返回筛选需要的字段
                return self._filter_model_info_for_api(model_info)
            except Exception as e:
                logger.error(f"Error loading model info from {model_info_path}: {e}")
                # 如果读取失败但是是默认模型，则返回默认配置
                if model_id == "default_model":
                    logger.info(f"Returning default info for model: {model_id}")
                    return self._filter_model_info_for_api(self.default_model_config)
        elif model_id == "default_model":
            logger.info(f"Info file not found, returning default info for model: {model_id}")
            return self._filter_model_info_for_api(self.default_model_config)
            
        logger.warning(f"Model info not found for model: {model_id}")
        return None
    
    def _ensure_complete_model_info(self, model_info: Dict, model_id: str) -> Dict:
        """
        确保模型信息包含所有必要字段
        
        Args:
            model_info: 从文件读取的模型信息
            model_id: 模型ID
            
        Returns:
            Dict: 补充完整的模型信息
        """
        # 创建一个默认模型信息的副本
        complete_info = self.default_model_config.copy()
        
        # 用提供的模型信息覆盖默认值
        for key, value in model_info.items():
            if key in complete_info and isinstance(value, dict) and isinstance(complete_info[key], dict):
                # 如果是嵌套字典，递归合并
                for sub_key, sub_value in value.items():
                    complete_info[key][sub_key] = sub_value
            else:
                complete_info[key] = value
        
        # 确保至少有正确的ID
        complete_info["id"] = model_id
        
        # 复制metrics字段到_internal_metrics
        if "metrics" in model_info:
            complete_info["_internal_metrics"] = model_info["metrics"]
        
        return complete_info
    
    def _filter_model_info_for_api(self, model_info: Dict) -> Dict:
        """
        筛选API返回的模型信息字段，仅保留名称、描述和创建时间
        
        Args:
            model_info: 完整的模型信息
            
        Returns:
            Dict: 筛选后的模型信息
        """
        # 创建一个新的字典，只包含我们需要显示的字段
        filtered_info = {
            "id": model_info.get("id", ""),
            "name": model_info.get("name", ""),
            "description": model_info.get("description", ""),
            "created_at": model_info.get("created_at", "")
        }
        
        # 保留原始配置中的参数和配置信息，这些可能在其他地方需要使用
        if "parameters" in model_info:
            filtered_info["parameters"] = model_info["parameters"]
        if "config" in model_info:
            filtered_info["config"] = model_info["config"]
        if "metrics" in model_info:
            filtered_info["metrics"] = model_info["metrics"]
        if "_internal_metrics" in model_info:
            filtered_info["_internal_metrics"] = model_info["_internal_metrics"]
            
        return filtered_info
    
    def get_model_metrics(self, model_id: str) -> Dict:
        """
        获取指定模型的评估指标
        
        Args:
            model_id: 模型ID
            
        Returns:
            Dict: 评估指标
        """
        model_info = self.get_model_info(model_id)
        if model_info and "metrics" in model_info:
            logger.info(f"Returning metrics for model {model_id}: {model_info['metrics']}")
            return model_info["metrics"]
        elif model_info and "_internal_metrics" in model_info:
            logger.info(f"Returning internal metrics for model {model_id}")
            return model_info["_internal_metrics"]
        elif model_id == "default_model":
            logger.info(f"Returning default metrics for model {model_id}")
            return self.default_model_config.get("metrics", {})
        
        logger.warning(f"No metrics found for model {model_id}")
        return {}
    
    def load_model(self, model_id: str) -> Any:
        """
        加载指定的模型
        
        Args:
            model_id: 模型ID
            
        Returns:
            模型实例
        """
        if model_id in self.loaded_models:
            logger.info(f"Returning cached model: {model_id}")
            return self.loaded_models[model_id]
        
        # 根据模型ID确定模型文件路径
        model_path = None
        model_dir = os.path.join(self.models_dir, model_id)
        
        # 读取info.json文件以获取模型文件名
        info_path = os.path.join(model_dir, "info.json")
        model_filename = None
        
        if os.path.exists(info_path):
            try:
                with open(info_path, 'r', encoding='utf-8') as f:
                    model_info = json.load(f)
                    if "model_filename" in model_info:
                        model_filename = model_info["model_filename"]
                        logger.info(f"Model filename from info.json: {model_filename}")
            except Exception as e:
                logger.warning(f"Could not read model filename from info.json: {e}")
        
        # 查找模型文件
        if model_filename and os.path.exists(os.path.join(model_dir, model_filename)):
            model_path = os.path.join(model_dir, model_filename)
        else:
            # 尝试常见的模型文件名
            common_names = ["best_model.pt", "2.pt", "model.pt", "checkpoint.pt"]
            for name in common_names:
                potential_path = os.path.join(model_dir, name)
                if os.path.exists(potential_path):
                    model_path = potential_path
                    break
        
        # 如果在模型目录中找不到模型文件，尝试默认位置
        if not model_path:
            if model_id == "default_model":
                default_paths = [
                    os.path.join(self.models_dir, "best_model.pt"),
                    os.path.join(self.models_dir, "default_model", "best_model.pt"),
                    os.path.join(os.path.dirname(os.path.dirname(self.models_dir)), "checkpoints", "best_model.pt")
                ]
                
                for path in default_paths:
                    if os.path.exists(path):
                        model_path = path
                        break
        
        if not model_path or not os.path.exists(model_path):
            error_msg = f"找不到模型文件: {model_id}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.info(f"加载模型: {model_path}")
        
        try:
            # 添加 Fullmodel 到安全全局变量列表
            torch.serialization.add_safe_globals([Fullmodel])
            
            # 加载模型参数和配置，设置 weights_only=False
            model = torch.load(model_path, map_location=self.device, weights_only=False)
            
            # 确保模型在正确的设备上并设置为评估模式
            model = model.to(self.device)
            model.eval()
            
            # 缓存已加载的模型
            self.loaded_models[model_id] = model
            
            logger.info(f"模型 {model_id} 成功加载")
            return model
        except Exception as e:
            logger.error(f"加载模型 {model_id} 错误: {e}")
            raise
    
    def predict(self, model_id: str, input_data: np.ndarray) -> Dict[str, Any]:
        """
        使用指定模型进行预测
        
        Args:
            model_id: 模型ID
            input_data: 输入数据
            
        Returns:
            Dict: 预测结果
        """
        logger.info(f"开始使用模型 {model_id} 进行预测")
        logger.info(f"输入数据形状: {input_data.shape}, 数据类型: {input_data.dtype}")
        
        # 加载模型
        model = self.load_model(model_id)
        
        try:
            # 准备输入数据 - 处理为模型期望的格式
            # 为MRI重建创建坐标网格
            logger.info(f"处理前输入数据形状: {input_data.shape}")
            
            # 检查输入数据的维度，确保是二维数组
            if len(input_data.shape) > 2:
                # 如果是多维数组，尝试转换为二维
                # 可能是RGB图像，取第一个通道或转为灰度
                if len(input_data.shape) == 3 and input_data.shape[2] in [1, 3, 4]:
                    # 是图像格式 (H, W, C)，转换为灰度
                    if input_data.shape[2] == 1:
                        input_data = input_data[:, :, 0]  # 取第一个通道
                    else:
                        # 转换为灰度，使用简单平均法
                        input_data = np.mean(input_data, axis=2)
                else:
                    # 其他情况，取第一个合适的2D切片
                    for i in range(len(input_data.shape) - 1):
                        if input_data.shape[i] > 1 and input_data.shape[i+1] > 1:
                            # 找到合适的2D切片
                            slicing = [0] * len(input_data.shape)
                            slicing[i] = slice(None)
                            slicing[i+1] = slice(None)
                            input_data = input_data[tuple(slicing)]
                            break
            
            logger.info(f"处理后输入数据形状: {input_data.shape}")
            
            # 确保输入数据是二维的
            if len(input_data.shape) != 2:
                raise ValueError(f"无法处理形状为 {input_data.shape} 的输入数据。需要2D数据。")
                
            height, width = input_data.shape
            y_coords = np.linspace(-1, 1, height)
            x_coords = np.linspace(-1, 1, width)
            
            # 创建网格坐标
            grid_x, grid_y = np.meshgrid(x_coords, y_coords)
            
            # 将坐标展平并堆叠
            grid_coords = np.stack([grid_x.flatten(), grid_y.flatten()], axis=1)
            
            # 转换为torch张量
            coords_tensor = torch.from_numpy(grid_coords).float().to(self.device)
            
            logger.info(f"准备的输入坐标形状: {coords_tensor.shape}")
            
            # 执行预测
            with torch.no_grad():
                prediction = model(coords_tensor)
                logger.info(f"原始预测形状: {prediction.shape}")
            
            # 处理预测结果
            pred_complex = prediction[:, 0] + 1j * prediction[:, 1]
            pred_complex = pred_complex.reshape(height, width).cpu().numpy()
            
            # 获取幅值作为结果图像
            result_image = np.abs(pred_complex)
            
            # 归一化到0-1范围
            result_image = (result_image - result_image.min()) / (result_image.max() - result_image.min() + 1e-8)
            
            logger.info(f"结果图像形状: {result_image.shape}, 范围: [{result_image.min()}, {result_image.max()}]")
            
            # 获取评估指标
            metrics = self.get_model_metrics(model_id)
            
            # 返回结果
            return {
                "reconstructed_image": result_image,
                "metrics": {
                    "psnr": float(metrics.get("psnr", 0.0)),
                    "ssim": float(metrics.get("ssim", 0.0)),
                    "nse": float(metrics.get("nse", 0.0))
                }
            }
        except Exception as e:
            logger.error(f"使用模型 {model_id} 预测时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _get_original_image(self, model_id: str) -> Optional[np.ndarray]:
        """
        获取指定模型对应的原始图像
        
        Args:
            model_id: 模型ID
            
        Returns:
            np.ndarray: 原始图像
        """
        # 创建一个默认原始图像
        return np.ones((256, 256), dtype=np.float32)

# 创建全局模型服务实例
model_service = ModelService() 