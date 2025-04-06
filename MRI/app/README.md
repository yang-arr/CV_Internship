# MRI重建系统

基于隐式神经表示（INR）的二维MRI图像重建系统。

## 功能特性

- 用户管理：注册、登录、JWT身份验证
- 图像上传：支持上传MRI图像进行处理
- 图像重建：基于INR模型进行MRI图像重建
- 模型管理：模型加载、预测和结果处理
- WebSocket通信：实时推理进度与结果通知

## 技术栈

- FastAPI：高性能的Web框架
- SQLAlchemy：ORM数据库操作
- Jinja2：HTML模板引擎
- JWT：用户身份验证
- Uvicorn：ASGI服务器

## 安装依赖

```bash
pip install fastapi uvicorn sqlalchemy pymysql python-jose[cryptography] passlib[bcrypt] python-multipart pydantic[email] jinja2
```

## 启动应用

```bash
python -m MRI.app.main
```

应用将在以下地址运行：
- 本地访问: http://127.0.0.1:8000
- API文档: http://127.0.0.1:8000/docs

## API接口

### 认证相关

- POST /api/auth/register - 用户注册
- POST /api/auth/token - 用户登录，获取令牌
- GET /api/auth/me - 获取当前用户信息

### MRI重建相关

- POST /api/upload/image - 上传MRI图像
- POST /api/reconstruction/process - 处理MRI图像
- GET /api/reconstruction/results/{task_id} - 获取重建结果

## 页面路由

- / - 首页
- /login - 登录页面
- /register - 注册页面

## 数据库配置

数据库配置在`config.ini`文件中，包含以下设置：

```ini
[database]
DB_USER = 用户名
DB_PASSWORD = 密码
DB_HOST = 主机地址
DB_PORT = 端口
DB_NAME = 数据库名

[app]
SECRET_KEY = JWT密钥
``` 