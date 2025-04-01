# 图像处理与知识库系统

## 项目简介
本项目是一个基于 FastAPI 的图像处理系统，集成了图像上传、处理和知识库管理功能。系统支持多种图像处理模型，并提供知识库功能用于管理和分享文章。

## 功能特点
- 图像上传和处理
- 多种图像处理模型支持
- 用户认证和授权
- 知识库系统
  - 文章管理
  - 分类管理
  - 标签管理
  - Markdown 支持
  - 文章权限控制

## 系统要求
- Python 3.8+
- MySQL 5.7+
- 足够的磁盘空间用于存储图像和模型文件

## 安装步骤

### 1. 克隆项目
```bash
git clone [项目地址]
cd [项目目录]
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置数据库
1. 创建 MySQL 数据库：
```sql
CREATE DATABASE image_processing CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 配置数据库连接：
   - 复制 `config.ini.example` 为 `config.ini`
   - 修改数据库配置：
```ini
[database]
DB_USER = your_username
DB_PASSWORD = your_password
DB_HOST = localhost
DB_PORT = 3306
DB_NAME = image_processing
```

### 5. 配置模型
1. 下载模型文件：
   - 从 [模型下载地址] 下载所需的模型文件
   - 将模型文件放在 `app/models` 目录下

2. 配置模型参数：
   - 在 `config.ini` 中设置模型参数：
```ini
[models]
YOLO_MODEL_PATH = app/models/yolov8n.pt
YOLO_CONFIDENCE = 0.25
```

### 6. 启动应用
```bash
python main.py
```

## 使用说明

### 1. 用户管理
- 注册新用户：访问 `http://localhost:8000/static/register.html`
- 用户登录：访问 `http://localhost:8000/static/login.html`

### 2. 图像处理
- 上传图像：访问 `http://localhost:8000/static/upload.html`
- 查看处理结果：访问 `http://localhost:8000/static/results.html`

### 3. 知识库系统
- 知识库首页：访问 `http://localhost:8000/static/knowledge.html`
- 文章管理：
  - 创建文章：点击"新建文章"按钮
  - 编辑文章：在文章列表点击"编辑"按钮
  - 删除文章：在文章列表点击"删除"按钮
- 分类管理：
  - 创建分类：点击"新建分类"按钮
  - 编辑分类：在分类列表点击"编辑"按钮
  - 删除分类：在分类列表点击"删除"按钮
- 标签管理：
  - 创建标签：点击"新建标签"按钮
  - 编辑标签：在标签列表点击"编辑"按钮
  - 删除标签：在标签列表点击"删除"按钮

### 4. API 文档
- Swagger UI：访问 `http://localhost:8000/docs`
- ReDoc：访问 `http://localhost:8000/redoc`

## 目录结构
```
app/
├── database/          # 数据库相关
│   ├── db.py         # 数据库配置和基础模型
│   └── models.py     # 数据模型定义
├── models/           # 模型文件目录
├── routers/          # 路由处理
│   ├── image_router.py
│   ├── user_router.py
│   ├── websocket_router.py
│   └── knowledge_router.py
├── static/           # 静态文件
│   ├── css/
│   ├── js/
│   └── images/
└── templates/        # HTML 模板
```

## 数据库模型

### 用户模型 (User)
- id: 主键
- username: 用户名
- email: 邮箱
- hashed_password: 加密密码
- created_at: 创建时间
- updated_at: 更新时间

### 图像模型 (Image)
- id: 主键
- user_id: 用户ID
- filename: 文件名
- original_path: 原始图像路径
- processed_path: 处理后图像路径
- file_size: 文件大小
- mime_type: 文件类型
- width: 图像宽度
- height: 图像高度
- created_at: 创建时间

### 推理结果模型 (InferenceResult)
- id: 主键
- image_id: 图像ID
- model_name: 模型名称
- result_data: 结果数据
- confidence: 置信度
- processing_time: 处理时间
- status: 状态
- error_message: 错误信息
- created_at: 创建时间

### 知识库模型
#### 分类模型 (Category)
- id: 主键
- name: 分类名称
- description: 分类描述
- created_at: 创建时间
- updated_at: 更新时间

#### 文章模型 (Article)
- id: 主键
- title: 文章标题
- content: 文章内容
- summary: 文章摘要
- category_id: 分类ID
- author_id: 作者ID
- created_at: 创建时间
- updated_at: 更新时间
- view_count: 浏览次数
- is_published: 是否发布

#### 标签模型 (Tag)
- id: 主键
- name: 标签名称
- created_at: 创建时间

## 注意事项
1. 确保数据库配置正确
2. 确保模型文件已正确下载和配置
3. 确保有足够的磁盘空间
4. 定期备份数据库
5. 在生产环境中修改默认密码和密钥

## 常见问题
1. 数据库连接失败
   - 检查数据库配置
   - 确保数据库服务正在运行
   - 检查数据库用户权限

2. 模型加载失败
   - 检查模型文件是否存在
   - 检查模型文件路径配置
   - 确保有足够的内存

3. 文件上传失败
   - 检查文件大小限制
   - 检查文件类型限制
   - 检查磁盘空间

## 贡献指南
1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证
[许可证类型]

## 联系方式
[联系方式] 