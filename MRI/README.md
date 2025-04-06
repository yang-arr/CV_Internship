# 🧠 INR-MRI-Reconstruction

## 📝 项目概述

本项目是一个基于隐式神经表示（Implicit Neural Representation, INR）技术的二维MRI图像重建系统。随着医疗隐私保护意识的增强以及MRI成像过程中采集时间较长的限制，传统深度学习重建方法因依赖大量配对的欠采样与全采样数据，面临数据获取成本高、泛化能力不足等问题。为应对上述挑战，本项目引入隐式神经表示技术，设计了一种基于自监督学习的二维MRI图像重建方法。在显著提升高度欠采样条件下图像重建质量的同时，该方法亦有助于提高MRI系统的采集效率，具有良好的临床应用前景。

## 🚀 快速开始

### 环境要求

- Python 3.8+
- CUDA 11.7+ (GPU加速，可选)
- 8GB+ RAM

### 安装依赖

1. 克隆仓库

```bash
git clone https://github.com/yourusername/INR-MRI-Reconstruction.git
cd INR-MRI-Reconstruction
```

2. 创建虚拟环境 (可选但推荐)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 安装依赖包

```bash
pip install -r requirements.txt
```

### 运行系统

1. 启动Web服务

```bash
python -m app.main
```

2. 访问Web界面

打开浏览器，访问 http://localhost:8000 即可使用系统

## 📚 功能详解

### 1. 模型训练

本项目使用基于SIREN (Sinusoidal Representation Networks) 的隐式神经表示模型，通过以下命令训练模型：

```bash
python start.py
```

训练参数可在 `config.yaml` 文件中配置。

### 2. 图像重建

系统支持通过Web界面上传MRI图像并进行重建：

1. 上传欠采样MRI图像
2. 选择预训练模型
3. 点击"开始重建"按钮
4. 查看重建结果和评估指标

### 3. 性能评估

系统使用多种评价指标评估重建质量：

- PSNR (Peak Signal-to-Noise Ratio)
- SSIM (Structural Similarity Index)
- NSE (Normalized Squared Error)

## 🔧 技术栈

### 后端

- FastAPI: 高性能Web框架
- PyTorch: 深度学习框架
- OpenCV: 图像处理库
- NumPy/SciPy: 科学计算库

### 前端

- HTML5/CSS3/JavaScript: 前端基础技术
- Bootstrap 5: 响应式UI框架
- WebSocket: 实时通信

### 算法

- INR (Implicit Neural Representation): 隐式神经表示
- SIREN: 周期性激活函数网络
- Fourier Feature Mapping: 傅里叶特征映射

## 📂 项目结构

```
INR-MRI-Reconstruction/
├── app/                    # Web应用目录
│   ├── api/                # API路由
│   ├── core/               # 核心功能
│   ├── models/             # 数据模型
│   ├── services/           # 服务层
│   ├── static/             # 静态文件
│   ├── templates/          # HTML模板
│   ├── utils/              # 工具函数
│   └── main.py             # 应用入口
├── models/                 # 预训练模型存储
├── uploads/                # 上传文件临时存储
├── dataset.py              # 数据集处理
├── model.py                # 模型定义
├── train.py                # 训练过程
├── main.py                 # 训练入口
├── config.yaml             # 配置文件
├── requirements.txt        # 依赖列表
└── README.md               # 项目说明
```

## 📡 API参考

系统提供以下主要API：

### 模型管理

- `GET /api/models/` - 获取所有可用模型列表
- `GET /api/models/{model_id}` - 获取特定模型详情

### 图像重建

- `POST /api/reconstruction/` - 提交重建请求
- `GET /api/reconstruction/models` - 获取可用的重建模型

### 文件上传

- `POST /api/upload/` - 上传文件
- `POST /api/upload/images/` - 上传并预处理图像

### WebSocket

- `WS /api/ws/{client_id}` - 建立WebSocket连接，接收实时状态更新

## 🚢 部署指南

### Docker部署

1. 构建Docker镜像

```bash
docker build -t inr-mri-reconstruction .
```

2. 运行容器

```bash
docker run -d -p 8000:8000 --name mri-recon inr-mri-reconstruction
```

### 服务器部署

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 使用Gunicorn和Uvicorn启动服务

```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 👨‍💻 贡献指南

欢迎贡献代码、报告问题或提出改进建议！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## ❓ 常见问题

### Q: 如何添加新的模型?
A: 将训练好的模型放入 `models` 目录下对应的子目录中，并确保包含必要的元数据文件。

### Q: 支持哪些图像格式?
A: 系统支持PNG、JPG、BMP等常见图像格式，以及DICOM医学影像格式。

### Q: 如何调整模型参数?
A: 修改 `config.yaml` 文件中的相关参数，然后重新训练模型。

## 📜 许可证

本项目采用 MIT 许可证 - 详细信息请查看 [LICENSE](LICENSE) 文件 