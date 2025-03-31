import os
import uuid
import logging
from typing import Tuple, Optional, Dict, Any
from datetime import datetime
from PIL import Image, ImageOps, UnidentifiedImageError
import numpy as np
import io

# 创建日志记录器
logger = logging.getLogger("image_utils")

class ImageProcessor:
    """
    图像处理工具类，处理各种图像操作
    """
    
    @staticmethod
    def validate_image(image_data: bytes) -> Tuple[bool, str]:
        """
        验证图像数据是否有效
        
        Args:
            image_data (bytes): 图像二进制数据
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            img.verify()  # 验证图像数据
            return True, ""
        except Exception as e:
            return False, f"无效的图像数据: {str(e)}"
    
    @staticmethod
    def get_image_info(image: Image.Image) -> Dict[str, Any]:
        """
        获取图像信息
        
        Args:
            image (PIL.Image.Image): 图像对象
            
        Returns:
            Dict[str, Any]: 图像信息
        """
        return {
            "format": image.format,
            "mode": image.mode,
            "width": image.width,
            "height": image.height,
            "size": image.width * image.height
        }
    
    @staticmethod
    def save_image(image_data: bytes, directory: str = "app/static/uploads") -> Tuple[str, str]:
        """
        保存图像文件
        
        Args:
            image_data (bytes): 图像二进制数据
            directory (str): 保存目录
            
        Returns:
            Tuple[str, str]: (文件名, 文件路径)
        """
        # 确保目录存在
        os.makedirs(directory, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}.jpg"
        filepath = os.path.join(directory, filename)
        
        try:
            # 打开图像
            img = Image.open(io.BytesIO(image_data))
            
            # 转换模式
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # 保存图像
            img.save(filepath, "JPEG")
            logger.info(f"图像已保存: {filepath}")
            
            return filename, filepath
        except Exception as e:
            logger.error(f"保存图像时出错: {str(e)}")
            raise
    
    @staticmethod
    def load_image(filepath: str) -> Optional[Image.Image]:
        """
        从文件加载图像
        
        Args:
            filepath (str): 图像文件路径
            
        Returns:
            Optional[PIL.Image.Image]: 加载的图像，加载失败则返回None
        """
        try:
            img = Image.open(filepath)
            # 转换为RGB模式（如果需要）
            if img.mode != "RGB":
                img = img.convert("RGB")
            return img
        except UnidentifiedImageError:
            logger.error(f"无法识别的图像格式: {filepath}")
            return None
        except Exception as e:
            logger.error(f"加载图像时出错: {filepath}, {str(e)}")
            return None
    
    @staticmethod
    def preprocess_image(img: Image.Image, target_size: Tuple[int, int] = (224, 224)) -> Image.Image:
        """
        预处理图像（调整大小、裁剪等）
        
        Args:
            img (PIL.Image.Image): 原始图像
            target_size (Tuple[int, int]): 目标尺寸
            
        Returns:
            PIL.Image.Image: 预处理后的图像
        """
        # 创建副本以避免修改原图
        img_copy = img.copy()
        
        # 调整图像尺寸（保持纵横比）
        img_copy.thumbnail(target_size, Image.LANCZOS)
        
        # 如果图像尺寸与目标尺寸不匹配，则使用居中裁剪或填充
        if img_copy.size != target_size:
            # 填充模式
            img_copy = ImageOps.pad(img_copy, target_size, centering=(0.5, 0.5))
        
        return img_copy
    
    @staticmethod
    def normalize_image(img: Image.Image) -> np.ndarray:
        """
        将图像归一化为numpy数组
        
        Args:
            img (PIL.Image.Image): 输入图像
            
        Returns:
            np.ndarray: 归一化后的图像数组
        """
        # 转换为numpy数组
        img_array = np.array(img).astype(np.float32)
        
        # 归一化到[0, 1]范围
        img_array = img_array / 255.0
        
        # 或使用标准化（ImageNet标准）
        # mean = np.array([0.485, 0.456, 0.406])
        # std = np.array([0.229, 0.224, 0.225])
        # img_array = (img_array - mean) / std
        
        return img_array 