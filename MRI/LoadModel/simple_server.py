import http.server
import socketserver
import json
import os
from pathlib import Path
import shutil

PORT = 8000

# 确保存在正确的模型文件
def ensure_model_files():
    """确保模型文件和信息文件存在并且正确"""
    app_models_dir = Path("../app/models")
    default_model_dir = app_models_dir / "default_model"
    checkpoints_dir = Path("checkpoints")
    
    # 确保目录存在
    os.makedirs(default_model_dir, exist_ok=True)
    
    # 检查并更新 info.json 文件
    info_file = default_model_dir / "info.json"
    model_info = {
        "name": "默认MRI重建模型",
        "description": "基于隐式神经表示的MRI重建模型",
        "created_at": "2023-04-06T13:45:00Z",
        "parameters": {
            "input_size": 256,
            "output_size": 256,
            "model_type": "SIREN"
        },
        "metrics": {
            "psnr": 32.5,
            "ssim": 0.9450,
            "nse": 0.9850
        },
        "config": {
            "encoder": {
                "encoding_mode": "fourier",
                "in_features": 2,
                "out_features": 20,
                "coordinate_scales": [1.0, 1.0]
            },
            "mlp": {
                "mlp_hidden_features": 256,
                "mlp_hidden_layers": 4,
                "omega_0": 30,
                "activation": "sine"
            }
        }
    }
    
    with open(info_file, "w") as f:
        json.dump(model_info, f, indent=4)
    
    # 检查并复制模型文件
    if not os.path.exists(default_model_dir / "best_model.pt") or os.path.getsize(default_model_dir / "best_model.pt") < 1000000:
        if os.path.exists(checkpoints_dir / "best_model.pt"):
            shutil.copy2(checkpoints_dir / "best_model.pt", default_model_dir / "best_model.pt")
            print(f"已复制模型文件到 {default_model_dir / 'best_model.pt'}")
        else:
            print("警告: 未找到 checkpoints/best_model.pt 文件!")
    
    # 创建模型列表 API 响应
    api_dir = Path("api")
    os.makedirs(api_dir, exist_ok=True)
    
    models_api_file = api_dir / "models.json"
    models_data = {
        "models": [model_info]
    }
    
    with open(models_api_file, "w") as f:
        json.dump(models_data, f, indent=4)
    
    print("模型文件和信息已准备就绪")

# 创建自定义处理程序
class ModelServerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 处理 API 请求
        if self.path == "/api/models":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            with open("api/models.json", "rb") as f:
                self.wfile.write(f.read())
            return
        
        # 默认行为：提供静态文件
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

# 主函数
def main():
    # 确保模型文件存在
    ensure_model_files()
    
    # 启动 HTTP 服务器
    with socketserver.TCPServer(("", PORT), ModelServerHandler) as httpd:
        print(f"服务器运行在 http://localhost:{PORT}")
        print("按 Ctrl+C 停止服务器")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("服务器已停止")

if __name__ == "__main__":
    main() 