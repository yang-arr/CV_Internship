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
uvicorn MRI.main:app --reload
```

### 访问入口
- Web界面: http://localhost:8000
- API文档: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws
- 监控面板: http://localhost:8000/monitor

### 快速测试
```bash
# 测试API服务
curl http://localhost:8000/health

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

### 开发者功能
| 功能 | 描述 | 技术特点 |
|------|------|----------|
| 模型扩展 | 支持自定义模型添加 | 模块化设计 |
| API集成 | RESTful API & WebSocket | 标准化接口 |
| 配置管理 | JSON格式配置文件 | 灵活配置 |
| 性能优化 | GPU加速支持 | 高性能计算 |
| 日志系统 | 完整的日志记录 | 问题追踪 |
| 测试框架 | 单元测试和集成测试 | 质量保证 |

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI
  - 异步支持
  - 自动API文档
  - 高性能路由
- **深度学习**: PyTorch
  - 自定义模型支持
  - GPU加速
  - 模型导出
- **数据库**: SQLAlchemy + PostgreSQL
  - 关系型数据存储
  - 事务支持
  - 数据迁移
- **图像处理**: Pillow, NumPy
  - 图像格式转换
  - 数据预处理
  - 结果后处理

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
- **交互**: jQuery
  - DOM操作
  - 事件处理
  - AJAX请求

## 📁 项目结构
```mermaid
graph TD
    A[MRI] --> B[app]
    A --> C[LoadModel]
    A --> D[models]
    A --> E[tests]
    B --> F[api]
    B --> G[services]
    B --> H[static]
    B --> I[templates]
    B --> J[utils]
    F --> K[auth.py]
    F --> L[model_management.py]
    F --> M[reconstruction.py]
    F --> N[websocket.py]
    G --> O[model_service.py]
    G --> P[task_service.py]
    G --> Q[db.py]
    G --> R[auth.py]
    H --> S[css]
    H --> T[js]
    H --> U[images]
    I --> V[auth]
    I --> W[models]
    I --> X[reconstruction]
    I --> Y[tasks]
```

## 📚 API文档

### 认证接口
```http
POST /auth/register
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
```

### 重建接口
```http
POST /reconstruction
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
```

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

### WebSocket接口
```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// 监听消息
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Task update:', data);
};

// 发送消息
ws.send(JSON.stringify({
    type: 'subscribe',
    task_id: 'task_123'
}));
```

完整API文档: [API Reference](docs/api.md)

## 🚢 部署指南

### 开发环境
```bash
# 使用开发服务器
uvicorn MRI.main:app --reload --host 0.0.0.0 --port 8000

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
gunicorn -w $WORKERS -k uvicorn.workers.UvicornWorker MRI.main:app \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

# 3. 配置Nginx
location / {
    proxy_pass http://localhost:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Docker部署
```bash
# 构建镜像
docker build -t mri-reconstruction .

# 运行容器
docker run -d \
    -p 8000:8000 \
    -e DATABASE_URL=postgresql://user:password@db:5432/dbname \
    -e SECRET_KEY=your_secret_key \
    mri-reconstruction
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
A: 在 `models` 目录下创建新文件夹，添加模型文件和 `info.json` 配置。

Q: 模型加载失败怎么办？  
A: 检查模型文件路径、格式和CUDA可用性。

Q: 如何评估模型性能？  
A: 使用内置的评估工具，支持PSNR、SSIM、NSE等指标。

### 性能相关
Q: 如何提高重建速度？  
A: 启用GPU加速，优化批处理大小。

Q: 内存不足怎么办？  
A: 减小批处理大小，使用轻量级模型。

Q: 如何优化系统性能？  
A: 使用缓存、异步处理、负载均衡等技术。

### 部署相关
Q: 如何配置HTTPS？  
A: 使用Nginx配置SSL证书，设置反向代理。

Q: 如何备份数据？  
A: 定期备份数据库，使用对象存储保存模型文件。

Q: 如何监控系统状态？  
A: 使用内置的监控面板，配置告警规则。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 📝 更新日志

### 2024-06-15
- 🧭 **优化导航栏**：提升系统整体用户体验
  - 在登录页面和注册页面添加统一的导航栏，保持风格一致性
  - 确保所有页面都能轻松访问系统主要功能包括数据看板
  - 优化页面布局，防止导航栏遮挡内容
  - 统一图标样式，提升界面美观度

### 2024-04-11
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
3. 访问 http://localhost:8000/medical-qa 进入问答界面
4. 在输入框中输入您的医疗相关问题，或点击麦克风按钮使用语音输入
5. 点击发送或按回车键获取AI回答
6. 系统会自动朗读AI的回答，也可点击消息右侧的播放按钮重新播放

### API 接口
```http
# 文本问答
POST /api/medical/ask
Content-Type: application/json

{
    "text": "您的医疗问题"
}

Response:
{
    "response": "AI的回答内容"
}

# 语音转文本
POST /api/medical/speech-to-text
Content-Type: multipart/form-data

audio_file: [二进制音频文件]

Response:
{
    "text": "识别出的文本内容"
}

# 文本转语音
POST /api/medical/text-to-speech
Content-Type: application/json

{
    "text": "要转换为语音的文本",
    "lang": "zh",
    "slow": false
}

Response: 音频文件 (audio/mpeg)
```

### 注意事项
- 本功能仅供参考，不能替代专业医生的诊断和建议
- 请确保 Ollama 服务正常运行在默认端口 (11434)
- 语音识别需要浏览器支持和麦克风权限
- 语音合成质量依赖于浏览器或服务器的支持能力
- 如遇到问题，请检查网络连接和 Ollama 服务状态

## 🛠️ 问题修复记录

### 2024-07-XX: 修复了历史记录图片显示问题
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

## 主要功能

1. **MRI图像重建**
   - 支持不同重建模型的选择
   - 实时显示重建进度
   - 计算PSNR、SSIM等客观指标
   - 保存重建历史记录

2. **医学图像分析**（新增功能）
   - 脑体积异常检测：针对神经退行性疾病
   - 病灶检测：识别肿瘤/多发性硬化斑块等
   - 运动伪影检测：评估图像质量
   - 三维可视化：展示脑部结构和病灶位置
   - 异常预警系统：对检测到的异常进行提示
   - 分析报告导出：支持JSON格式（PDF格式即将推出）

3. **在线训练**
   - 上传自定义图像进行模型训练
   - 实时查看训练进度和损失曲线
   - 支持多种网络参数配置
   - 训练完成后可直接用于图像重建

4. **医疗智能问答**
   - 与AI医疗助手进行专业咨询
   - 获取医学影像相关知识

## 技术架构

### 前端
- HTML5 + CSS3 + Bootstrap 5
- JavaScript (ES6+)
- Chart.js：用于数据可视化
- Three.js：用于3D渲染

### 后端
- FastAPI：高性能Web框架
- SQLAlchemy：ORM数据库操作
- PyTorch：深度学习框架
- MONAI：医疗影像专用深度学习工具包

### 医学图像处理工具
- ANTsPy：高级神经影像工具
- SimpleITK：简化的影像工具包
- MONAI：医疗AI框架

## 安装与使用

1. 克隆仓库
```bash
git clone <repository-url>
cd mri-reconstruction-system
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 启动应用
```bash
python -m MRI.app.main
```

4. 访问系统
```
http://localhost:8001
```

## 医学图像分析功能使用指南

1. 在MRI重建界面完成图像重建后，系统会自动显示医学分析面板
2. 输入重建任务ID（或使用当前重建任务ID），点击"开始分析"
3. 系统会对重建图像进行多维度分析，包括脑体积测量、病灶检测和运动伪影评估
4. 分析完成后，可以查看不同类型的分析结果，包括数据表格和3D可视化
5. 点击"导出报告"可以导出分析结果，目前支持JSON格式

## 系统截图

*（此处可添加系统界面截图）*

## 贡献指南

欢迎参与项目开发，提交问题或贡献代码：

1. Fork本仓库
2. 创建新分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 提交Pull Request

## 许可证

本项目遵循 MIT 许可证