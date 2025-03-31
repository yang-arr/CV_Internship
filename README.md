# 图像处理与模型推理API

这是一个基于FastAPI构建的后端系统，提供图像上传、管理、使用预训练模型进行推理（分类）以及结果返回的功能。系统支持同步和异步推理，并通过WebSocket提供实时任务更新。

## 目录

1.  [功能特性](#功能特性)
2.  [技术栈](#技术栈)
3.  [项目结构](#项目结构)
4.  [安装与配置](#安装与配置)
    *   [前提条件](#前提条件)
    *   [安装步骤](#安装步骤)
    *   [配置说明 (`config.ini`)](#配置说明-configini)
5.  [运行应用](#运行应用)
6.  [API文档](#api文档)
7.  [API端点详解](#api端点详解)
    *   [用户认证](#用户认证)
    *   [图像管理](#图像管理)
    *   [模型推理](#模型推理)
    *   [WebSocket实时更新](#websocket实时更新)
8.  [使用示例](#使用示例)
    *   [用户注册与登录](#用户注册与登录)
    *   [上传图像](#上传图像)
    *   [执行同步推理](#执行同步推理)
    *   [执行异步推理并获取结果](#执行异步推理并获取结果)
    *   [通过WebSocket接收实时更新](#通过websocket接收实时更新)
9.  [扩展模型](#扩展模型)
10. [日志记录](#日志记录)
11. [许可证](#许可证)

## 功能特性

*   **用户管理**: 基于JWT的用户注册、登录和认证。
*   **图像管理**: 支持图像上传（带类型和大小校验）、查询、删除。
*   **模型推理**: 
    *   调用预训练模型对上传的图像进行处理和推理。
    *   支持 **同步** 推理：立即返回结果。
    *   支持 **异步** 推理：提交任务后通过轮询或WebSocket获取结果，适合耗时较长的模型。
*   **结果存储**: 将图像信息和推理结果存储在MySQL数据库中。
*   **实时通知**: 使用WebSocket向客户端实时推送异步推理任务的状态更新。
*   **模块化设计**: 清晰的代码结构，易于维护和扩展。
*   **配置灵活**: 通过 `config.ini` 文件管理数据库连接、密钥等配置。
*   **API文档**: 自动生成交互式API文档 (Swagger UI / ReDoc)。

## 技术栈

*   **Web框架**: FastAPI
*   **数据库**: MySQL
*   **ORM**: SQLAlchemy
*   **异步任务**: FastAPI BackgroundTasks
*   **实时通信**: FastAPI WebSockets
*   **认证**: JWT (python-jose), Passlib (密码哈希)
*   **图像处理**: Pillow
*   **数据处理**: NumPy
*   **配置管理**: configparser
*   **依赖管理**: pip, requirements.txt

## 项目结构

```
├── app/
│   ├── database/           # 数据库相关 (模型定义, 连接)
│   │   ├── __init__.py
│   │   └── db.py
│   ├── models/             # AI模型接口与实现
│   │   ├── __init__.py
│   │   └── model_interface.py
│   ├── routers/            # API路由定义
│   │   ├── __init__.py
│   │   ├── image_router.py
│   │   ├── user_router.py
│   │   └── websocket_router.py
│   ├── schemas/            # Pydantic数据模型 (请求/响应验证)
│   │   ├── __init__.py
│   │   ├── image.py
│   │   └── user.py
│   ├── static/             # 静态文件 (上传的图像)
│   │   └── uploads/
│   └── utils/              # 工具函数与类
│       ├── __init__.py
│       ├── exceptions.py
│       ├── image_utils.py
│       └── logging_config.py
├── logs/                   # 日志文件目录
├── venv/                   # Python虚拟环境 (可选)
├── .env                    # 环境变量文件 (可选, 用于敏感信息)
├── .gitignore              # Git忽略文件配置
├── config.ini              # 应用配置文件
├── main.py                 # FastAPI应用入口
├── README.md               # 项目说明文件
└── requirements.txt        # Python依赖列表
```

## 安装与配置

### 前提条件

*   **Python**: 3.7 或更高版本。
*   **MySQL**: 5.7 或更高版本 (或其他兼容的数据库)。
*   **Git**: 用于克隆项目。
*   **pip**: Python包管理器。

### 安装步骤

1.  **克隆项目**: 
    ```bash
    git clone <your-repository-url> # 替换为你的仓库URL
    cd <repository-directory>
    ```

2.  **创建并激活虚拟环境** (推荐):
    ```bash
    python -m venv venv
    # Linux/macOS
    source venv/bin/activate
    # Windows (cmd/powershell)
    venv\Scripts\activate 
    ```

3.  **安装依赖**: 
    ```bash
    pip install -r requirements.txt
    ```

4.  **数据库设置**:
    *   确保你的MySQL服务正在运行。
    *   创建一个新的数据库（例如 `image_processing`）:
        ```sql
        CREATE DATABASE image_processing CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        ```
    *   **重要**: 根据你的MySQL配置，更新 `config.ini` 文件中的数据库连接信息。

### 配置说明 (`config.ini`)

`config.ini` 文件用于管理应用程序的配置。请根据你的环境修改此文件。

```ini
[database]
# 数据库用户名
DB_USER = root 
# 数据库密码 (如果密码为空，请留空)
DB_PASSWORD = 
# 数据库主机地址
DB_HOST = localhost
# 数据库端口
DB_PORT = 3306
# 数据库名称 (应与第4步创建的数据库名称一致)
DB_NAME = image_processing

[app]
# JWT签名密钥，请务必修改为一个强随机字符串！
SECRET_KEY = your_secret_key_for_jwt 
# 图像上传目录 (相对于项目根目录)
UPLOAD_DIR = app/static/uploads
# 最大上传文件大小 (字节, 默认为10MB)
MAX_UPLOAD_SIZE = 10485760  
# 是否启用调试模式 (True/False)
DEBUG = True
# 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = INFO 
```

**安全提示**: `SECRET_KEY` 是用于JWT令牌签名的关键密钥，**绝不要** 使用默认值或容易猜到的值。建议使用 `openssl rand -hex 32` 或类似工具生成一个安全的随机密钥。

## 运行应用

在项目根目录下，运行以下命令启动FastAPI服务：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

*   `--host 0.0.0.0`: 使服务可以通过网络访问（如果需要）。如果只想本地访问，可以使用 `127.0.0.1`。
*   `--port 8000`: 指定服务监听的端口。
*   `--reload`: 开发模式下启用自动重载，当代码更改时服务会自动重启。

服务启动后，你应该能看到类似以下的输出，并可以通过 `http://localhost:8000` (或你配置的地址和端口) 访问。

## API文档

应用启动后，可以通过浏览器访问自动生成的API文档：

*   **Swagger UI**: `http://localhost:8000/docs` (提供交互式测试界面)
*   **ReDoc**: `http://localhost:8000/redoc` (提供另一种风格的文档)

## API端点详解

### 用户认证

*   `POST /users/`: **创建新用户**。需要提供 `username`, `email`, `password`。
*   `POST /users/token`: **用户登录**。使用 `username` 和 `password` 进行表单提交，成功后返回 `access_token`。
*   `GET /users/me`: **获取当前用户信息**。需要提供有效的 `Authorization: Bearer <token>` 头。
*   `PUT /users/me`: **更新当前用户信息**。可以更新 `username`, `email`, `password`。需要提供有效的 `Authorization` 头。

### 图像管理

(以下端点均需要有效的 `Authorization: Bearer <token>` 头)

*   `POST /images/upload`: **上传图像文件**。使用 `multipart/form-data` 格式上传，字段名为 `file`。支持 `jpeg`, `png`, `bmp`, `gif` 格式，默认大小限制为10MB。
*   `GET /images/`: **获取当前用户上传的图像列表**。支持分页参数 `skip` 和 `limit`。
*   `GET /images/{image_id}`: **获取指定ID的图像信息**。
*   `DELETE /images/{image_id}`: **删除指定ID的图像** 及其关联的推理结果和物理文件。

### 模型推理

(以下端点均需要有效的 `Authorization: Bearer <token>` 头)

*   `POST /images/inference`: **执行同步推理**。
    *   请求体需要 `image_id` 和可选的 `model_name` (默认为 `dummy`)。
    *   立即返回推理结果，包括预测类别、置信度、处理时间等。
*   `POST /images/inference/async`: **执行异步推理**。
    *   请求体需要 `image_id` 和可选的 `model_name`。
    *   立即返回一个任务信息，包含 `task_id` 和状态查询URL。
    *   推理将在后台执行。
*   `GET /images/inference/tasks/{task_id}`: **获取异步推理任务的状态**。返回任务的当前状态 (`pending`, `processing`, `completed`, `failed`) 和结果URL（如果已完成）。
*   `GET /images/inference/{result_id}`: **获取指定ID的推理结果**。通常在异步任务完成后，通过任务状态中的 `result_url` 或直接使用结果ID访问。

### WebSocket实时更新

*   `ws://localhost:8000/ws/inference?token=YOUR_JWT_TOKEN`: **WebSocket连接端点**。
    *   需要提供有效的JWT令牌作为查询参数 `token`。
    *   连接成功后，服务器会实时推送该用户相关的异步推理任务的状态更新（任务完成或失败时）。

## 使用示例

以下是使用 `curl` 和 `websocat` (一个WebSocket客户端) 的基本示例。

### 用户注册与登录

```bash
# 1. 注册用户
curl -X POST "http://localhost:8000/users/" \
     -H "Content-Type: application/json" \
     -d '{
           "username": "testuser", 
           "email": "test@example.com", 
           "password": "testpassword123"
         }'

# 2. 用户登录获取Token
TOKEN=$(curl -X POST "http://localhost:8000/users/token" \
             -H "Content-Type: application/x-www-form-urlencoded" \
             -d "username=testuser&password=testpassword123" | jq -r .access_token)

echo "Access Token: $TOKEN"
```

### 上传图像

```bash
# 假设你有一个名为 image.jpg 的图片文件
curl -X POST "http://localhost:8000/images/upload" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@image.jpg"
# 记下返回结果中的 image_id
```

### 执行同步推理

```bash
# 假设上传图像的 ID 为 1
IMAGE_ID=1
curl -X POST "http://localhost:8000/images/inference" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"image_id": '$IMAGE_ID', "model_name": "dummy"}'
```

### 执行异步推理并获取结果

```bash
# 1. 提交异步任务
TASK_INFO=$(curl -X POST "http://localhost:8000/images/inference/async" \
                 -H "Authorization: Bearer $TOKEN" \
                 -H "Content-Type: application/json" \
                 -d '{"image_id": '$IMAGE_ID', "model_name": "dummy"}')

TASK_ID=$(echo $TASK_INFO | jq -r .task_id)
TASK_URL="http://localhost:8000$(echo $TASK_INFO | jq -r .result_url)"

echo "Task ID: $TASK_ID"
echo "Task Status URL: $TASK_URL"

# 2. 轮询任务状态 (重复执行直到状态变为 completed 或 failed)
sleep 5 # 等待任务处理
curl -H "Authorization: Bearer $TOKEN" $TASK_URL

# 3. (任务完成后) 获取结果
# 假设上一步返回的 result_url 是 /images/inference/2
RESULT_URL="http://localhost:8000/images/inference/2"
curl -H "Authorization: Bearer $TOKEN" $RESULT_URL
```

### 通过WebSocket接收实时更新

你需要一个WebSocket客户端，例如 `websocat`。

```bash
# 使用之前获取的 $TOKEN
websocat "ws://localhost:8000/ws/inference?token=$TOKEN"

# 现在，如果你提交一个新的异步推理任务，
# 当任务完成或失败时，你会在此连接中收到JSON格式的通知。
```

## 扩展模型

系统设计允许轻松添加新的推理模型。

1.  **创建模型类**: 在 `app/models/` 目录下创建一个新的Python文件（例如 `app/models/resnet_model.py`）。
2.  **继承接口**: 让你的新模型类继承自 `app.models.model_interface.ModelInterface`。
3.  **实现方法**: 实现 `ModelInterface` 要求的所有抽象方法：
    *   `load_model()`: 加载模型文件和权重。
    *   `preprocess(image)`: 对输入的Pillow图像对象进行预处理（调整大小、归一化等），返回模型期望的输入格式。
    *   `predict(processed_data)`: 执行模型推理，返回原始预测结果。
    *   `postprocess(prediction)`: 对原始预测结果进行后处理，返回统一格式的字典（包含类别、置信度等）。
4.  **注册模型**: 打开 `app/models/model_interface.py` 文件，在 `create_model()` 函数中，添加一个 `elif` 分支来实例化你的新模型类。给你的模型起一个唯一的名字（例如 `resnet50`）。

```python
# 在 app/models/model_interface.py 的 create_model 函数中添加
# ... (之前的代码)
elif model_name == "resnet50":
    from .resnet_model import ResNetModel # 导入你的新模型类
    model = ResNetModel()
# ... (之后的代码)
```

5.  **使用新模型**: 现在，你可以在进行推理请求时，通过 `model_name` 参数指定使用你的新模型了（例如 `"model_name": "resnet50"`）。

## 日志记录

*   应用程序的日志配置在 `app/utils/logging_config.py` 中定义。
*   日志同时输出到控制台和文件。
*   日志文件存储在项目根目录下的 `logs/` 目录中，按日期轮转。
*   日志级别可以在 `config.ini` 文件中配置 (`LOG_LEVEL`)。

## 许可证

本项目采用 [MIT许可证](LICENSE)。 