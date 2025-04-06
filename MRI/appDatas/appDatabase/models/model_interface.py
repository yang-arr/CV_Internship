import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import json
from PIL import Image

# 创建日志记录器
logger = logging.getLogger("model_interface")

class ModelInterface(ABC):
    """
    模型接口抽象基类，所有模型实现必须继承此类
    """
    
    @abstractmethod
    def load_model(self) -> bool:
        """
        加载模型
        
        Returns:
            bool: 加载是否成功
        """
        pass
        
    @abstractmethod
    def preprocess(self, image: Image.Image) -> Any:
        """
        预处理图像
        
        Args:
            image (PIL.Image.Image): 输入图像
            
        Returns:
            Any: 预处理后的数据
        """
        pass
        
    @abstractmethod
    def predict(self, processed_data: Any) -> Dict[str, Any]:
        """
        执行模型推理
        
        Args:
            processed_data (Any): 预处理后的数据
            
        Returns:
            Dict[str, Any]: 推理结果
        """
        pass
        
    @abstractmethod
    def postprocess(self, prediction: Any) -> Dict[str, Any]:
        """
        后处理推理结果
        
        Args:
            prediction (Any): 模型的原始推理结果
            
        Returns:
            Dict[str, Any]: 处理后的结果
        """
        pass
    
    def inference(self, image: Image.Image) -> Tuple[Dict[str, Any], float]:
        """
        执行完整的推理流程：预处理、推理、后处理
        
        Args:
            image (PIL.Image.Image): 输入图像
            
        Returns:
            Tuple[Dict[str, Any], float]: (处理结果, 处理时间)
        """
        start_time = time.time()
        
        try:
            # 预处理
            processed_data = self.preprocess(image)
            
            # 推理
            raw_prediction = self.predict(processed_data)
            
            # 后处理
            result = self.postprocess(raw_prediction)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            return result, processing_time
        
        except Exception as e:
            logger.error(f"推理过程中出错: {str(e)}")
            processing_time = time.time() - start_time
            return {"error": str(e)}, processing_time


class DummyModel(ModelInterface):
    """
    占位模型实现，用于测试和开发
    """
    
    def __init__(self):
        self.name = "dummy_model"
        self.model = None
        self.classes = ["类别1", "类别2", "类别3", "类别4", "类别5"]
        logger.info("初始化占位模型")
        
    def load_model(self) -> bool:
        """
        加载占位模型
        
        Returns:
            bool: 始终返回True
        """
        logger.info("加载占位模型")
        self.model = "dummy_model_loaded"
        return True
        
    def preprocess(self, image: Image.Image) -> np.ndarray:
        """
        对图像进行预处理（缩放、归一化等）
        
        Args:
            image (PIL.Image.Image): 输入图像
            
        Returns:
            np.ndarray: 预处理后的图像数组
        """
        # 调整图像尺寸到224x224（常见的预处理尺寸）
        image = image.resize((224, 224))
        
        # 转换为numpy数组并归一化
        img_array = np.array(image) / 255.0
        
        logger.info(f"图像预处理完成，形状: {img_array.shape}")
        return img_array
        
    def predict(self, processed_data: np.ndarray) -> np.ndarray:
        """
        使用占位模型进行推理
        
        Args:
            processed_data (np.ndarray): 预处理后的图像数据
            
        Returns:
            np.ndarray: 模拟的推理结果
        """
        # 模拟推理延迟
        time.sleep(0.5)
        
        # 生成随机概率分布
        np.random.seed(int(time.time()))
        predictions = np.random.rand(len(self.classes))
        predictions = predictions / np.sum(predictions)  # 归一化，使总和为1
        
        logger.info(f"占位模型推理完成，结果形状: {predictions.shape}")
        return predictions
        
    def postprocess(self, prediction: np.ndarray) -> Dict[str, Any]:
        """
        后处理推理结果
        
        Args:
            prediction (np.ndarray): 模型的原始推理结果
            
        Returns:
            Dict[str, Any]: 处理后的结果
        """
        # 获取Top-3的预测结果
        indices = np.argsort(prediction)[::-1][:3]
        top_classes = [self.classes[i] for i in indices]
        top_probs = [float(prediction[i]) for i in indices]
        
        result = {
            "top_predictions": [
                {"class": cls, "probability": prob} 
                for cls, prob in zip(top_classes, top_probs)
            ],
            "top_class": top_classes[0],
            "confidence": float(top_probs[0])
        }
        
        logger.info(f"后处理完成，预测类别: {result['top_class']}")
        return result


# 工厂函数，用于创建模型实例
def create_model(model_name: str = "dummy") -> ModelInterface:
    """
    根据名称创建模型实例
    
    Args:
        model_name (str): 模型名称
        
    Returns:
        ModelInterface: 模型接口实例
    """
    if model_name == "dummy":
        model = DummyModel()
    # 这里可以添加更多模型实现
    # elif model_name == "resnet50":
    #     model = ResNet50Model()
    # elif model_name == "efficientnet":
    #     model = EfficientNetModel()
    else:
        logger.warning(f"未知模型: {model_name}，使用占位模型")
        model = DummyModel()
    
    # 加载模型
    model.load_model()
    
    return model 