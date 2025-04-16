#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
医学图像分析API路由
包含对重建MRI图像进行医学分析的接口
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status, Path
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
import os
import uuid
import numpy as np
from datetime import datetime
import base64
from PIL import Image
import io
import json
import aiofiles

from MRI.app.services.db import get_db
from MRI.app.services.auth import get_current_user
from MRI.app.models.user import User
from MRI.app.models.reconstruction_history import ReconstructionHistory
from sqlalchemy.orm import Session

# 尝试导入医学图像处理库
try:
    import SimpleITK as sitk
    import ants
    import monai
    from monai.transforms import (
        LoadImaged, 
        EnsureChannelFirstd, 
        Orientationd,
        ScaleIntensityd,
        ToTensord
    )
    from monai.inferers import sliding_window_inference
    from monai.networks.nets import UNet
    import torch
    
    MEDICAL_LIBS_AVAILABLE = True
except ImportError:
    MEDICAL_LIBS_AVAILABLE = False
    logging.warning("医学图像处理库未完全安装，将使用模拟分析功能")

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter()

# 定义全局变量存储模型
BRAIN_SEGMENTATION_MODEL = None
LESION_DETECTION_MODEL = None
MOTION_ARTIFACT_MODEL = None

# 加载分析模型
def load_analysis_models():
    """加载医学分析模型"""
    global BRAIN_SEGMENTATION_MODEL, LESION_DETECTION_MODEL, MOTION_ARTIFACT_MODEL
    
    if not MEDICAL_LIBS_AVAILABLE:
        logger.warning("无法加载医学分析模型：缺少必要的库")
        return
    
    try:
        # 脑部分割模型
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 使用MONAI加载预训练模型
        BRAIN_SEGMENTATION_MODEL = UNet(
            spatial_dims=3,
            in_channels=1,
            out_channels=4,  # 背景、灰质、白质、脑脊液
            channels=(16, 32, 64, 128, 256),
            strides=(2, 2, 2, 2),
        ).to(device)
        
        # 此处应加载预训练权重，示例代码：
        # model_weights_path = os.path.join("MRI", "app", "models", "weights", "brain_segmentation.pth")
        # if os.path.exists(model_weights_path):
        #     BRAIN_SEGMENTATION_MODEL.load_state_dict(torch.load(model_weights_path, map_location=device))
        
        # 病灶检测模型
        LESION_DETECTION_MODEL = UNet(
            spatial_dims=3,
            in_channels=1,
            out_channels=2,  # 背景、病灶
            channels=(16, 32, 64, 128, 256),
            strides=(2, 2, 2, 2),
        ).to(device)
        
        # 运动伪影检测模型 - 使用简单分类网络
        MOTION_ARTIFACT_MODEL = monai.networks.nets.DenseNet121(
            spatial_dims=3, 
            in_channels=1, 
            out_channels=2  # 有伪影/无伪影
        ).to(device)
        
        logger.info("医学分析模型加载成功")
    except Exception as e:
        logger.error(f"加载医学分析模型时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())

# 模拟分析函数（用于演示）
def simulate_analysis(image_path):
    """模拟医学图像分析，返回分析结果"""
    # 图像路径为None时仍然可以进行模拟分析
    if image_path and os.path.exists(image_path):
        logger.info(f"使用图像进行模拟分析: {image_path}")
        # 可以用图像路径做一些简单的图像处理，这里简化处理
    else:
        logger.warning("未提供有效图像路径，使用完全模拟分析")
    
    # 生成模拟数据
    # 脑体积分析结果
    volume_analysis = {
        "total_volume": round(np.random.uniform(1100, 1400), 2),  # 单位：cm³
        "gray_matter": round(np.random.uniform(600, 700), 2),
        "white_matter": round(np.random.uniform(400, 500), 2),
        "csf": round(np.random.uniform(100, 200), 2),
        "normal_range": {
            "total_volume": [1100, 1400],
            "gray_matter": [600, 700],
            "white_matter": [400, 500],
            "csf": [100, 200]
        },
        "abnormal": np.random.random() < 0.3  # 30%概率异常
    }
    
    # 病灶检测结果
    lesion_detection = {
        "lesions_count": int(np.random.randint(0, 5)),
        "total_volume": round(np.random.uniform(0, 10), 2),
        "locations": [],
        "confidence": round(np.random.uniform(80, 99), 1),
        "abnormal": False
    }
    
    # 添加模拟病灶位置
    if lesion_detection["lesions_count"] > 0:
        for i in range(lesion_detection["lesions_count"]):
            lesion_detection["locations"].append({
                "x": int(np.random.randint(10, 100)),
                "y": int(np.random.randint(10, 100)),
                "z": int(np.random.randint(10, 50)),
                "size": round(np.random.uniform(0.1, 2.0), 2),
                "confidence": round(np.random.uniform(70, 99), 1)
            })
        lesion_detection["abnormal"] = True
    
    # 运动伪影检测结果
    motion_detection = {
        "has_artifact": np.random.random() < 0.2,  # 20%概率有伪影
        "severity": round(np.random.uniform(0, 10), 1),
        "confidence": round(np.random.uniform(80, 99), 1),
        "abnormal": False
    }
    
    if motion_detection["has_artifact"] and motion_detection["severity"] > 3:
        motion_detection["abnormal"] = True
    
    # 综合分析结果
    analysis_results = {
        "volume_analysis": volume_analysis,
        "lesion_detection": lesion_detection,
        "motion_detection": motion_detection,
        "abnormalities": [],
        "alert_level": "normal",  # normal, warning, alert
        "diagnosis": "正常",
        "visualization_data": {
            "brain_mesh": generate_mock_brain_mesh(),
            "lesion_mesh": generate_mock_lesion_mesh() if lesion_detection["lesions_count"] > 0 else None
        }
    }
    
    # 整合异常情况
    if volume_analysis["abnormal"]:
        analysis_results["abnormalities"].append({
            "type": "脑体积异常",
            "value": volume_analysis["total_volume"],
            "normal_range": volume_analysis["normal_range"]["total_volume"],
            "confidence": 95.5
        })
        analysis_results["alert_level"] = "warning"
        analysis_results["diagnosis"] = "脑体积异常，可能与神经退行性疾病相关"
    
    if lesion_detection["abnormal"]:
        analysis_results["abnormalities"].append({
            "type": "检测到病灶",
            "value": lesion_detection["total_volume"],
            "count": lesion_detection["lesions_count"],
            "confidence": lesion_detection["confidence"]
        })
        analysis_results["alert_level"] = "alert"
        analysis_results["diagnosis"] = f"检测到 {lesion_detection['lesions_count']} 个可疑病灶，建议进一步检查"
    
    if motion_detection["abnormal"]:
        analysis_results["abnormalities"].append({
            "type": "运动伪影",
            "value": motion_detection["severity"],
            "confidence": motion_detection["confidence"]
        })
        if analysis_results["alert_level"] == "normal":
            analysis_results["alert_level"] = "warning"
            analysis_results["diagnosis"] = "图像中检测到运动伪影，可能影响诊断准确性"
    
    return analysis_results

# 生成模拟的3D网格数据（用于前端可视化）
def generate_mock_brain_mesh():
    """生成模拟脑部3D网格数据"""
    vertices = []
    faces = []
    
    # 生成一个简单的球形数据作为脑部模型
    radius = 50
    stacks = 20
    slices = 20
    
    # 生成顶点
    for stack in range(stacks + 1):
        phi = stack * np.pi / stacks
        for slice in range(slices):
            theta = slice * 2 * np.pi / slices
            x = radius * np.sin(phi) * np.cos(theta)
            y = radius * np.sin(phi) * np.sin(theta)
            z = radius * np.cos(phi)
            vertices.append([float(x), float(y), float(z)])
    
    # 生成面
    for stack in range(stacks):
        for slice in range(slices):
            p1 = stack * slices + slice
            p2 = p1 + 1
            if slice == slices - 1:
                p2 = stack * slices
            p3 = p1 + slices
            p4 = p2 + slices
            
            if p4 >= len(vertices):
                p4 = p4 % len(vertices)
            if p3 >= len(vertices):
                p3 = p3 % len(vertices)
            
            faces.append([p1, p2, p3])
            faces.append([p2, p4, p3])
    
    return {"vertices": vertices, "faces": faces}

def generate_mock_lesion_mesh():
    """生成模拟病灶3D网格数据"""
    vertices = []
    faces = []
    
    # 生成一个简单的球形数据作为病灶模型
    radius = 5
    stacks = 10
    slices = 10
    center = [np.random.randint(-30, 30), np.random.randint(-30, 30), np.random.randint(-30, 30)]
    
    # 生成顶点
    for stack in range(stacks + 1):
        phi = stack * np.pi / stacks
        for slice in range(slices):
            theta = slice * 2 * np.pi / slices
            x = radius * np.sin(phi) * np.cos(theta) + center[0]
            y = radius * np.sin(phi) * np.sin(theta) + center[1]
            z = radius * np.cos(phi) + center[2]
            vertices.append([float(x), float(y), float(z)])
    
    # 生成面
    for stack in range(stacks):
        for slice in range(slices):
            p1 = stack * slices + slice
            p2 = p1 + 1
            if slice == slices - 1:
                p2 = stack * slices
            p3 = p1 + slices
            p4 = p2 + slices
            
            if p4 >= len(vertices):
                p4 = p4 % len(vertices)
            if p3 >= len(vertices):
                p3 = p3 % len(vertices)
            
            faces.append([p1, p2, p3])
            faces.append([p2, p4, p3])
    
    return {"vertices": vertices, "faces": faces}

# 分析重建图像
@router.post("/analyze/{task_id}")
async def analyze_image(
    task_id: str = Path(..., description="重建任务ID"),
    analysis_type: str = Form(..., description="分析类型：full, volume, lesion, motion"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """分析重建后的MRI图像"""
    try:
        # 检查分析类型是否有效
        valid_types = ["full", "volume", "lesion", "motion"]
        if analysis_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"不支持的分析类型。有效类型: {', '.join(valid_types)}")
            
        # 查找重建结果图像
        reconstructed_image_dir = os.path.join("MRI", "app", "uploads", "reconstructed")
        reconstructed_image_path = os.path.join(reconstructed_image_dir, f"{task_id}.png")
        
        if not os.path.exists(reconstructed_image_path):
            # 查找替代位置 - 可能是在历史记录中
            history_record = db.query(ReconstructionHistory).filter(
                ReconstructionHistory.task_id == task_id,
                ReconstructionHistory.user_id == current_user.id
            ).first()
            
            if history_record and history_record.reconstructed_image_path and os.path.exists(history_record.reconstructed_image_path):
                reconstructed_image_path = history_record.reconstructed_image_path
                logger.info(f"从历史记录中找到重建图像: {reconstructed_image_path}")
            else:
                # 仍然找不到图像，使用模拟分析
                logger.warning(f"未找到重建图像，将使用模拟分析: {task_id}")
                # 生成一个空的模拟图像用于分析
                analysis_results = simulate_analysis(None)
                
                # 保存分析结果
                analysis_result_dir = os.path.join("MRI", "app", "results", "analysis")
                os.makedirs(analysis_result_dir, exist_ok=True)
                result_file_path = os.path.join(analysis_result_dir, f"{task_id}.json")
                
                with open(result_file_path, 'w', encoding='utf-8') as f:
                    json.dump(analysis_results, f, ensure_ascii=False, indent=2)
                
                logger.info(f"模拟分析完成，结果已保存: {result_file_path}")
                
                return JSONResponse(
                    content={
                        "success": True,
                        "task_id": task_id,
                        "analysis_type": analysis_type,
                        "results": analysis_results,
                        "warning": "未找到重建图像，使用模拟分析"
                    },
                    status_code=200
                )
        
        logger.info(f"开始分析MRI图像: {task_id}, 分析类型: {analysis_type}, 用户ID: {current_user.id}")
        
        # TODO: 根据医学图像处理库是否可用，选择真实分析或模拟分析
        # 目前使用模拟分析作为演示
        analysis_results = simulate_analysis(reconstructed_image_path)
        
        # 保存分析结果
        analysis_result_dir = os.path.join("MRI", "app", "results", "analysis")
        os.makedirs(analysis_result_dir, exist_ok=True)
        result_file_path = os.path.join(analysis_result_dir, f"{task_id}.json")
        
        with open(result_file_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"图像分析完成，结果已保存: {result_file_path}")
        
        return JSONResponse(
            content={
                "success": True,
                "task_id": task_id,
                "analysis_type": analysis_type,
                "results": analysis_results
            },
            status_code=200
        )
    except HTTPException as http_ex:
        # 已经是HTTPException，直接抛出
        logger.error(f"HTTP异常: {http_ex.detail}")
        raise
    except Exception as e:
        logger.error(f"分析图像时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={
                "success": False,
                "message": f"分析失败: {str(e)}"
            },
            status_code=500
        )

# 获取分析结果
@router.get("/analysis/{task_id}")
async def get_analysis_result(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取之前保存的分析结果"""
    try:
        # 查找分析结果文件
        analysis_result_dir = os.path.join("MRI", "app", "results", "analysis")
        result_file_path = os.path.join(analysis_result_dir, f"{task_id}.json")
        
        logger.info(f"尝试获取分析结果: {task_id}, 用户ID: {current_user.id}")
        
        if not os.path.exists(result_file_path):
            logger.warning(f"分析结果文件不存在，尝试即时分析: {task_id}")
            # 如果结果不存在，执行模拟分析
            reconstructed_image_dir = os.path.join("MRI", "app", "uploads", "reconstructed")
            reconstructed_image_path = os.path.join(reconstructed_image_dir, f"{task_id}.png")
            
            if not os.path.exists(reconstructed_image_path):
                logger.error(f"重建图像不存在: {task_id}")
                return JSONResponse(
                    content={
                        "success": False,
                        "message": "重建图像不存在，无法进行分析"
                    },
                    status_code=404
                )
            
            # 执行模拟分析
            logger.info(f"开始即时模拟分析: {reconstructed_image_path}")
            analysis_results = simulate_analysis(reconstructed_image_path)
            
            # 保存分析结果
            os.makedirs(analysis_result_dir, exist_ok=True)
            with open(result_file_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"即时分析完成，结果已保存: {result_file_path}")
            
            return JSONResponse(
                content={
                    "success": True,
                    "task_id": task_id,
                    "results": analysis_results,
                    "note": "结果通过即时分析生成"
                },
                status_code=200
            )
        
        # 读取分析结果
        try:
            with open(result_file_path, 'r', encoding='utf-8') as f:
                analysis_results = json.load(f)
            
            logger.info(f"获取分析结果成功: {task_id}")
            
            return JSONResponse(
                content={
                    "success": True,
                    "task_id": task_id,
                    "results": analysis_results
                },
                status_code=200
            )
        except json.JSONDecodeError as json_err:
            logger.error(f"JSON解析错误: {json_err}, 文件: {result_file_path}")
            return JSONResponse(
                content={
                    "success": False,
                    "message": f"分析结果文件格式错误: {str(json_err)}"
                },
                status_code=500
            )
    except Exception as e:
        logger.error(f"获取分析结果时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={
                "success": False,
                "message": f"获取分析结果失败: {str(e)}"
            },
            status_code=500
        )

# 导出分析报告
@router.get("/report/{task_id}")
async def export_analysis_report(
    task_id: str,
    report_format: str = "json", 
    current_user: User = Depends(get_current_user)
):
    """导出分析报告（JSON或PDF）"""
    try:
        # 查找分析结果文件
        analysis_result_dir = os.path.join("MRI", "app", "results", "analysis")
        result_file_path = os.path.join(analysis_result_dir, f"{task_id}.json")
        
        if not os.path.exists(result_file_path):
            raise HTTPException(status_code=404, detail="分析结果不存在")
        
        # 读取分析结果
        with open(result_file_path, 'r', encoding='utf-8') as f:
            analysis_results = json.load(f)
        
        if report_format.lower() == "json":
            return analysis_results
        elif report_format.lower() == "pdf":
            # TODO: 实现PDF报告生成
            # 这里只返回一个提示信息
            return {
                "success": False,
                "message": "PDF报告生成功能即将推出"
            }
        else:
            raise HTTPException(status_code=400, detail=f"不支持的报告格式: {report_format}")
    except Exception as e:
        logger.error(f"导出分析报告时出错: {e}")
        raise HTTPException(status_code=500, detail=f"导出分析报告失败: {str(e)}")

# 添加新接口：通过上传文件直接分析图像
@router.post("/analyze-upload")
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    analysis_type: str = Form(..., description="分析类型：full, volume, lesion, motion"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """通过上传文件直接分析MRI图像"""
    try:
        # 检查文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="仅支持图像文件")
        
        # 检查分析类型是否有效
        valid_types = ["full", "volume", "lesion", "motion"]
        if analysis_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"不支持的分析类型。有效类型: {', '.join(valid_types)}")
        
        # 生成临时任务ID
        task_id = str(uuid.uuid4())
        logger.info(f"开始分析上传的MRI图像: {task_id}, 分析类型: {analysis_type}, 用户ID: {current_user.id}")
        
        # 保存上传的图像
        upload_dir = os.path.join("MRI", "app", "uploads", "analysis")
        os.makedirs(upload_dir, exist_ok=True)
        image_path = os.path.join(upload_dir, f"{task_id}.png")
        
        # 读取和保存图像
        try:
            contents = await file.read()
            if not contents:
                raise ValueError("上传的文件内容为空")
                
            # 确保文件是有效的图像
            try:
                img = Image.open(io.BytesIO(contents))
                img.verify()  # 验证图像完整性
                logger.info(f"图像验证通过: 格式={img.format}, 大小={img.size}")
            except Exception as img_err:
                logger.error(f"图像验证失败: {img_err}")
                raise ValueError(f"无效的图像文件: {str(img_err)}")
                
            async with aiofiles.open(image_path, 'wb') as f:
                await f.write(contents)
                
            logger.info(f"图像已保存到: {image_path}")
        except Exception as file_err:
            logger.error(f"保存上传图像时出错: {file_err}")
            raise ValueError(f"文件保存失败: {str(file_err)}")
        
        # 模拟分析
        logger.info(f"开始模拟分析: {image_path}")
        analysis_results = simulate_analysis(image_path)
        
        # 保存分析结果
        analysis_result_dir = os.path.join("MRI", "app", "results", "analysis")
        os.makedirs(analysis_result_dir, exist_ok=True)
        result_file_path = os.path.join(analysis_result_dir, f"{task_id}.json")
        
        with open(result_file_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"上传图像分析完成，结果已保存: {result_file_path}")
        
        return JSONResponse(
            content={
                "success": True,
                "task_id": task_id,
                "analysis_type": analysis_type,
                "results": analysis_results
            },
            status_code=200
        )
    except HTTPException as http_ex:
        # 已经是HTTPException，直接抛出
        logger.error(f"HTTP异常: {http_ex.detail}")
        raise
    except Exception as e:
        logger.error(f"分析上传图像时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={
                "success": False,
                "message": f"分析失败: {str(e)}"
            },
            status_code=500
        )

# 启动时加载模型
@router.on_event("startup")
async def startup_event():
    """应用启动时加载分析模型"""
    load_analysis_models() 