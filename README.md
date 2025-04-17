# 🧠 "智绘影"MRI重建系统

基于隐式神经表示（INR）的二维MRI图像重建系统，提供图像重建、在线训练、医疗问答等功能。

## 项目简介

"智绘影"MRI重建系统是一个专为医学影像处理设计的平台，利用先进的深度学习技术对MRI图像进行重建和分析。系统旨在提高MRI采集效率，减少采集时间，同时保证重建图像的质量。

### 系统特点
- 高精度重建：PSNR > 30dB，SSIM > 0.9
- 实时处理：单张图像处理时间 < 1s
- 可扩展架构：支持自定义模型和算法
- 安全可靠：完整的用户认证和权限控制
- 易于部署：支持Docker容器化部署

## 🚀 快速开始

### 环境要求
- Python 3.8+
- CUDA 11.0+ (可选，用于GPU加速)
- 4GB+ RAM
- 2GB+ 磁盘空间
- NVIDIA GPU (推荐，用于加速计算)

### 安装步骤
```bash
# 1. 克隆仓库
git clone [repository_url]
cd MRI

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python -m MRI.app.services.db init_db

# 5. 启动服务
python -m MRI.app.main
```

### 访问入口
- Web界面: http://localhost:8001
- API文档: http://localhost:8001/about
- 监控面板: http://localhost:8001/monitor

### 快速测试
```bash
# 测试API服务
curl http://localhost:8001/health

# 测试模型服务
python -m MRI.app.services.model_service test_model default_model
```

## ✨ 功能特性

### 用户功能
| 功能 | 描述 | 使用场景 |
|------|------|----------|
| 用户认证 | 注册、登录、密码重置 | 系统访问控制 |
| 模型管理 | 查看、选择、评估模型 | 模型选择和优化 |
| 图像重建 | 上传、处理、预览结果 | 医学图像处理 |
| 在线训练 | 上传图像训练自定义模型 | 个性化模型定制 |
| 任务追踪 | 实时查看处理进度 | 批量任务管理 |
| 结果分析 | 图像质量评估和对比 | 结果验证 |
| 数据导出 | 支持多种格式导出 | 数据共享和备份 |
| 医疗问答 | 智能医疗咨询 | 专业知识获取 |
| 医学图像分析 | 异常检测和病灶识别 | 临床辅助诊断 |
| 用户反馈 | 问题报告和建议提交 | 系统改进 |
| 数据看板 | 数据统计和趋势分析 | 使用情况监控 |

### 开发者功能
| 功能 | 描述 | 技术特点 |
|------|------|----------|
| 模型扩展 | 支持自定义模型添加 | 模块化设计 |
| API集成 | RESTful API & WebSocket | 标准化接口 |
| 配置管理 | YAML格式配置文件 | 灵活配置 |
| 性能优化 | GPU加速支持 | 高性能计算 |
| 日志系统 | 完整的日志记录 | 问题追踪 |
| 测试框架 | 单元测试和集成测试 | 质量保证 |
| 权限控制 | 基于角色的访问控制 | 安全保障 |
| 插件系统 | 支持功能扩展 | 灵活扩展 |

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI
  - 异步支持
  - 自动API文档
  - 高性能路由
  - 依赖注入
- **深度学习**: PyTorch
  - 自定义模型支持
  - GPU加速
  - 模型导出
  - 在线训练
- **数据库**: SQLAlchemy + PostgreSQL
  - 关系型数据存储
  - 事务支持
  - 数据迁移
  - ORM映射
- **图像处理**: 
  - Pillow, OpenCV: 基础图像处理
  - NumPy, SciPy: 数学计算
  - scikit-image: 高级图像处理
  - MONAI: 医学图像专用工具
  - SimpleITK: 医学影像处理

### 前端
- **UI框架**: Bootstrap 5
  - 响应式设计
  - 主题定制
  - 组件库
- **实时通信**: WebSocket
  - 实时数据更新
  - 双向通信
  - 断线重连
- **图表**: Chart.js
  - 数据可视化
  - 实时更新
  - 交互式图表
- **3D可视化**: Three.js
  - 三维渲染
  - 交互式医学图像展示
- **用户交互**: 
  - jQuery: DOM操作
  - ES6+: 现代JavaScript
  - Fetch API: 网络请求

## 📁 项目结构
```mermaid
graph TD
    MRI["MRI系统"] --> App["app (应用主目录)"]
    MRI --> LoadModel["LoadModel (模型加载与处理)"]
    MRI --> Models["models (预训练模型存储)"]
    MRI --> Uploads["uploads (上传文件存储)"]
    MRI --> Results["results (结果输出)"]
    
    App --> API["api (API接口)"]
    App --> AppModels["models (数据模型)"]
    App --> Schemas["schemas (数据验证模式)"]
    App --> Services["services (业务服务)"]
    App --> Static["static (静态资源)"]
    App --> Templates["templates (页面模板)"]
    App --> Main["main.py (应用入口)"]
    
    API --> Auth["auth.py (认证API)"]
    API --> Reconstruction["reconstruction.py (重建API)"]
    API --> MedicalQA["medical_qa.py (医疗问答API)"]
    API --> OnlineTraining["online_training.py (在线训练API)"]
    API --> MedicalAnalysis["medical_analysis.py (医学图像分析)"]
    API --> Upload["upload.py (文件上传)"]
    API --> WebSocket["websocket.py (实时通信)"]
    API --> Dashboard["dashboard.py (数据看板)"]
    API --> ReconstHist["reconstruction_history.py (重建历史)"]
    API --> Feedback["feedback.py (用户反馈)"]
    
    Services --> ModelService["model_service.py (模型服务)"]
    Services --> AuthService["auth.py (认证服务)"]
    Services --> DB["db.py (数据库服务)"]
    
    LoadModel --> ModelPy["model.py (模型定义)"]
    LoadModel --> DatasetPy["dataset.py (数据集处理)"]
    LoadModel --> TrainPy["train.py (训练脚本)"]
    LoadModel --> TestPy["test.py (测试脚本)"]
    LoadModel --> VisualizePy["visualize.py (可视化)"]
    
    Static --> CSS["css (样式表)"]
    Static --> JS["js (JavaScript)"]
    Static --> Img["img (图像资源)"]
    
    Templates --> IndexHTML["index.html (重建页面)"]
    Templates --> MedicalQAHTML["medical_qa.html (医疗问答页面)"]
    Templates --> OnlineTrainingHTML["online_training.html (在线训练页面)"]
    Templates --> DashboardHTML["dashboard.html (仪表盘页面)"]
    Templates --> LoginHTML["login.html (登录页面)"]
```

## 📚 API文档

### 认证接口
```http
POST /api/auth/register
Content-Type: application/json

{
    "username": "string",
    "email": "string",
    "password": "string"
}

Response:
{
    "id": "string",
    "username": "string",
    "email": "string",
    "created_at": "datetime"
}

POST /api/auth/login
Content-Type: application/json

{
    "username": "string",
    "password": "string"
}

Response:
{
    "access_token": "string",
    "token_type": "bearer",
    "user": {
        "id": "string",
        "username": "string",
        "email": "string",
        "role": "string"
    }
}
```

### 重建接口
```http
POST /api/reconstruction
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: binary
model_id: string
parameters: {
    "batch_size": 32,
    "use_gpu": true
}

Response:
{
    "task_id": "string",
    "status": "string",
    "estimated_time": "int"
}

GET /api/reconstruction/{task_id}
Authorization: Bearer {token}

Response:
{
    "task_id": "string",
    "status": "string",
    "progress": float,
    "result": {
        "original_image": "string",
        "reconstructed_image": "string",
        "metrics": {
            "psnr": float,
            "ssim": float
        }
    }
}
```

### 在线训练接口
```http
POST /api/online-training
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: binary
learning_rate: float
epochs: int
save_interval: int
use_gpu: boolean
encoder_mode: string
... (其他参数)

Response:
{
    "task_id": "string",
    "status": "submitted",
    "message": "训练任务已提交",
    "submit_time": "datetime"
}

GET /api/online-training/status/{task_id}
Authorization: Bearer {token}

Response:
{
    "task_id": "string",
    "status": "string", // running, completed, failed
    "progress": float,
    "current_epoch": int,
    "current_loss": float,
    ... (其他信息)
}
```

### 医疗问答接口
```http
POST /api/medical/ask
Authorization: Bearer {token}
Content-Type: application/json

{
    "text": "您的医疗问题"
}

Response:
{
    "response": "AI的回答内容"
}

POST /api/medical/speech-to-text
Content-Type: multipart/form-data

audio_file: [二进制音频文件]

Response:
{
    "text": "识别出的文本内容"
}

POST /api/medical/text-to-speech
Content-Type: application/json

{
    "text": "要转换为语音的文本",
    "lang": "zh",
    "slow": false
}

Response: 音频文件 (audio/mpeg)
```

### 医学图像分析接口
```http
POST /api/medical-analysis/analyze
Authorization: Bearer {token}
Content-Type: application/json

{
    "image_id": "string",
    "analysis_type": "brain_volume" // brain_volume, lesion_detection, motion_artifact
}

Response:
{
    "task_id": "string",
    "status": "submitted"
}

GET /api/medical-analysis/result/{task_id}
Authorization: Bearer {token}

Response:
{
    "task_id": "string",
    "status": "completed",
    "result": {
        "analysis_type": "brain_volume",
        "data": {
            // 分析结果数据，因分析类型而异
        },
        "warnings": [] // 潜在异常警告
    }
}
```

### WebSocket接口
```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8001/api/ws');

// 认证
ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'authenticate',
        token: 'your_access_token'
    }));
};

// 订阅任务更新
ws.send(JSON.stringify({
    type: 'subscribe',
    task_id: 'task_123'
}));

// 监听消息
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Task update:', data);
};
```

## 🚢 部署指南

### 开发环境
```bash
# 使用开发服务器
python -m MRI.app.main

# 启用调试模式
export DEBUG=true
export LOG_LEVEL=debug
```

### 生产环境
```bash
# 1. 配置环境变量
export DATABASE_URL=postgresql://user:password@localhost/dbname
export SECRET_KEY=your_secret_key
export REDIS_URL=redis://localhost:6379
export WORKERS=4
export LOG_LEVEL=info

# 2. 使用生产服务器
gunicorn -w $WORKERS -k uvicorn.workers.UvicornWorker MRI.app.main:app \
    --bind 0.0.0.0:8001 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

# 3. 配置Nginx
location / {
    proxy_pass http://localhost:8001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### Docker部署
```bash
# 构建镜像
docker build -t mri-reconstruction .

# 运行容器
docker run -d \
    -p 8001:8001 \
    -e DATABASE_URL=postgresql://user:password@db:5432/dbname \
    -e SECRET_KEY=your_secret_key \
    mri-reconstruction

# 使用Docker Compose
docker-compose up -d
```

## 🤝 贡献指南

### 开发流程
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范
- 遵循PEP 8规范
- 使用类型注解
- 编写单元测试
- 更新文档

### 提交规范
```
feat: 添加新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建过程或辅助工具的变动
```

## ❓ 常见问题

### 模型相关
Q: 如何添加新模型？  
A: 在 `models` 目录下添加模型文件，并在 `LoadModel/model.py` 中注册模型类。

Q: 模型加载失败怎么办？  
A: 检查模型文件路径、格式和CUDA可用性，确保系统环境与模型要求匹配。

Q: 如何评估模型性能？  
A: 使用系统内置的评估工具，支持PSNR、SSIM、NSE等指标，或使用Dashboard中的模型性能比较功能。

### 性能相关
Q: 如何提高重建速度？  
A: 启用GPU加速，优化批处理大小，考虑使用更轻量级的模型。

Q: 内存不足怎么办？  
A: 减小批处理大小，使用轻量级模型，增加系统内存或启用内存优化选项。

Q: 如何优化系统性能？  
A: 使用缓存、异步处理、负载均衡等技术，或者考虑分布式部署。

### 部署相关
Q: 如何配置HTTPS？  
A: 使用Nginx配置SSL证书，设置反向代理，或者使用Certbot等工具自动配置。

Q: 如何备份数据？  
A: 定期备份数据库，使用对象存储保存模型文件，或配置自动备份脚本。

Q: 如何监控系统状态？  
A: 使用内置的监控面板，配置告警规则，或集成第三方监控工具如Prometheus和Grafana。

## 🤖 医疗专家问答系统

### 功能介绍
- 基于 Ollama 本地部署的医疗专业大模型
- 实时问答交互界面
- 支持医疗咨询、诊断建议等功能
- ✨ **语音交互功能**：支持语音输入和语音朗读，提供更自然的交流体验

### 语音交互功能
- 🎙️ **语音输入**：点击麦克风按钮，通过语音提问问题
- 🔊 **语音播报**：系统自动朗读AI回答，方便用户接收信息
- 🎛️ **多重选项**：支持选择不同语音、调整语速和音调
- 💬 **混合交互**：可随时切换语音和文字输入方式
- 🔄 **备选方案**：当浏览器不支持语音API时，自动切换到服务器端语音处理

### 使用方法
1. 确保已安装并启动 Ollama 服务
2. 确保已加载 deepseek-r1-medical 模型
3. 访问 http://localhost:8001/medical-qa 进入问答界面
4. 在输入框中输入您的医疗相关问题，或点击麦克风按钮使用语音输入
5. 点击发送或按回车键获取AI回答
6. 系统会自动朗读AI的回答，也可点击消息右侧的播放按钮重新播放

## 📝 更新日志

### 2025-04-14: 修复了历史记录图片显示问题
- **问题描述**: 在查询图片重建历史记录时，原始图像和重建结果的图片无法正常加载
- **原因分析**: 在view_file API中，文件路径处理逻辑有限，只在uploads目录下查找文件
- **解决方案**: 
  1. 增强了view_file API的文件路径处理逻辑
  2. 添加了找不到图片时的优雅降级处理，显示"图片未找到"的默认图像
  3. 增加了多层级的文件路径解析，提高了文件查找的灵活性
- **修复文件**:
  - MRI/app/api/upload.py
  - MRI/app/static/img/image-not-found.png (新增)
- **效果**: 即使图片文件移动或丢失，系统仍然能够优雅地展示重建历史记录，提升了用户体验

### 2025-04-15
- 🧭 **优化导航栏**：提升系统整体用户体验
  - 在登录页面和注册页面添加统一的导航栏，保持风格一致性
  - 确保所有页面都能轻松访问系统主要功能包括数据看板
  - 优化页面布局，防止导航栏遮挡内容
  - 统一图标样式，提升界面美观度

### 2025-04-16
- 🔐 **修复认证系统**：解决了用户登录后立即返回登录页面的问题
  - 优化了token处理方式，同时支持从Cookie和Header获取token
  - 添加了前端认证管理模块，确保所有API请求附带正确的Authorization头
  - 实现了更可靠的错误处理机制，提升了系统稳定性
  - 优化了登录、登出流程，增强了用户体验

查看 [CHANGELOG.md](CHANGELOG.md) 了解更多更新。

## 📞 联系方式

- 项目维护者：王金洋 吴志宏 刘韬 普昊冕
- 邮箱：swuwjy08@email.swu.edu.cn
- 问题反馈：swuwjy08@email.swu.edu.cn
- 文档地址：https://github.com/yang-arr/CV_Internship
- 演示地址：https://github.com/yang-arr/CV_Internship

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)