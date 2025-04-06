from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ImageInfo(BaseModel):
    """图像信息的响应模式"""
    id: int
    filename: str
    original_path: str
    processed_path: Optional[str] = None
    file_size: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


class ImageCreate(BaseModel):
    """图像创建的内部模式（不直接接收请求）"""
    user_id: int
    filename: str
    original_path: str
    processed_path: Optional[str] = None
    file_size: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None


class ImageUploadResponse(BaseModel):
    """图像上传的响应模式"""
    id: int
    filename: str
    success: bool
    message: str
    image_url: str
    
    class Config:
        orm_mode = True


class InferenceRequest(BaseModel):
    """推理请求的模式"""
    image_id: int = Field(..., description="要进行推理的图像ID")
    model_name: str = Field("dummy", description="使用的模型名称")
    parameters: Optional[Dict[str, Any]] = Field(None, description="模型参数（如有）")


class PredictionResult(BaseModel):
    """预测结果的模式"""
    class_name: str
    probability: float


class InferenceResponse(BaseModel):
    """推理结果的响应模式"""
    id: int
    image_id: int
    model_name: str
    top_class: str
    confidence: float
    top_predictions: List[PredictionResult]
    processing_time: float
    status: str
    created_at: datetime
    
    class Config:
        orm_mode = True


class InferenceTaskResponse(BaseModel):
    """推理任务的响应模式（用于长时间运行的任务）"""
    task_id: str
    status: str
    image_id: int
    created_at: datetime
    result_url: Optional[str] = None 