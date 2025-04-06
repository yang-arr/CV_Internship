# 主程序文件：包含模型训练、验证和测试的主要流程
# 主要功能：
# 1. 参数配置和解析：从config.yaml读取训练参数
# 2. 数据加载和预处理：加载MRI数据集并进行预处理
# 3. 模型训练和验证：执行模型训练循环，包括损失计算和优化
# 4. 结果保存和可视化：保存模型检查点、最佳模型和训练曲线

import os
import yaml
import torch
import numpy as np
from torch.utils.data import Subset, DataLoader
from model import Fullmodel
from dataset import MRIDataset
from train import train_epoch_image
from visualize import save_epoch_results_as_png, save_best_image, plot_loss_curve


def save_checkpoint(model, optimizer, epoch, metrics, save_path):
    """保存模型检查点
    
    将模型状态、优化器状态和评估指标保存到指定路径
    
    Args:
        model: 训练好的模型
        optimizer: 优化器
        epoch: 当前训练轮数
        metrics: 包含PSNR和SSIM的评估指标字典
        save_path: 模型保存路径
    """
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'psnr': metrics['psnr'],
        'ssim': metrics['ssim']
    }
    torch.save(checkpoint, save_path)
    print(f"模型已保存到: {save_path}")


def load_best_metrics(metrics_path):
    """加载历史最佳指标
    
    Args:
        metrics_path: 指标文件路径
        
    Returns:
        tuple: (best_psnr, best_ssim)
    """
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                lines = f.readlines()
            best_psnr, best_ssim = 0, 0
            for line in lines:
                line = line.strip()
                if line.startswith("PSNR:"):
                    best_psnr = float(line.split("PSNR:")[-1].strip())
                elif line.startswith("SSIM:"):
                    best_ssim = float(line.split("SSIM:")[-1].strip())
            return best_psnr, best_ssim
        except Exception as e:
            print("读取best_metrics.txt出错，初始化best_psnr和best_ssim为0:", e)
            return 0, 0
    return 0, 0


def setup_device(gpu_id):
    """设置计算设备
    
    Args:
        gpu_id: GPU设备ID
        
    Returns:
        torch.device: 计算设备
    """
    if torch.cuda.is_available():
        device = torch.device(f'cuda:{gpu_id}')
        gpu_name = torch.cuda.get_device_name(gpu_id)
        print(f"Running on GPU {gpu_id}: {gpu_name}")
    else:
        device = torch.device('cpu')
        print("Running on CPU")
    return device


def main():
    """主函数：执行模型训练和验证的完整流程
    
    主要步骤：
    1. 加载配置文件
    2. 设置计算设备（GPU/CPU）
    3. 准备数据集和数据加载器
    4. 初始化模型和优化器
    5. 执行训练循环
    6. 保存训练结果和模型
    """
    # 加载配置文件
    with open("config.yaml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 设置计算设备
    device = setup_device(config['gpu_id'])

    # 准备数据集和数据加载器
    train_dataset = MRIDataset(config["dataset_path"], split='train')
    one_image_subset = Subset(train_dataset, [1])
    train_loader = DataLoader(one_image_subset, batch_size=1, shuffle=False)

    # 初始化模型
    model = Fullmodel(
        encoding_mode=config["encoder"]["encoding_mode"],
        in_features=config["encoder"]["in_features"],
        out_features=config["encoder"]["out_features"],
        coordinate_scales=config["encoder"]["coordinate_scales"],
        mlp_hidden_features=config["mlp"]["mlp_hidden_features"],
        mlp_hidden_layers=config["mlp"]["mlp_hidden_layers"],
        omega_0=config["mlp"]["omega_0"],
        activation=config["mlp"]["activation"],
    ).to(device)

    # 初始化优化器和学习率调度器
    optimizer = torch.optim.Adam(model.parameters(), lr=float(config["learning_rate"]))
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1000, gamma=0.9)

    # 初始化训练历史记录
    train_loss_history = []
    train_psnr_history = []
    
    # 设置结果保存目录
    result_dir = "{}_{}_{}_B_{}_{}".format(
        config['prediction_mode'],
        config['mlp']['activation'],
        config['encoder']['encoding_mode'],
        "TV" if config["use_tv"] else "NoTV",
        "penalty" if config["use_penalty"] else "No_penalty",
    )

    print("Result dir:", result_dir)

    # 创建模型保存目录
    model_save_dir = os.path.join(result_dir, "checkpoints")
    os.makedirs(model_save_dir, exist_ok=True)

    # 加载历史最佳指标
    best_metrics_path = os.path.join(result_dir, "best_metrics.txt")
    best_psnr, best_ssim = load_best_metrics(best_metrics_path)
    print("historial Best PSNR:", best_psnr, "Best SSIM:", best_ssim)

    # 开始训练循环
    print("Start Training!")
    for epoch in range(config["epochs"]):
        # 根据监督模式选择训练方法
        if config["supervision_mode"] in ['kspace', 'kspace_csm', 'image']:
            loss, psnr, ssim, nse = train_epoch_image(
                model, train_loader, optimizer, device,
                supervision_mode=config["supervision_mode"],
                lambda_tv=config["lambda_tv"]
            )
        else:
            raise ValueError("Unsupport Prediction_mode")

        # 记录训练历史
        train_loss_history.append(loss)
        train_psnr_history.append(psnr)
        sample = train_dataset[0]

        # 定期保存检查点和结果
        if (epoch + 1) % config.get("save_interval", 1000) == 0:
            save_epoch_results_as_png(
                model, sample, device, epoch, result_dir,
                supervision_mode=config["supervision_mode"]
            )
            checkpoint_path = os.path.join(model_save_dir, f"checkpoint_epoch_{epoch+1}.pt")
            save_checkpoint(model, optimizer, epoch, {'psnr': psnr, 'ssim': ssim}, checkpoint_path)
            print(
                f"Epoch {epoch + 1}/{config['epochs']}: Loss={loss:.4e}, "
                f"PSNR={psnr:.2f}, SSIM={ssim:.4f}, NSE={nse:.4f}"
            )
        
        # 保存性能提升时的最佳模型
        if psnr > best_psnr or ssim > best_ssim:
            best_psnr = max(best_psnr, psnr)
            best_ssim = max(best_ssim, ssim)
            save_best_image(
                model, sample, device, psnr, ssim, result_dir,
                supervision_mode=config["supervision_mode"]
            )
            best_model_path = os.path.join(model_save_dir, "best_model.pt")
            save_checkpoint(model, optimizer, epoch, {'psnr': psnr, 'ssim': ssim}, best_model_path)
        
        # 更新学习率
        scheduler.step()

    # 训练结束，保存最终模型
    final_model_path = os.path.join(model_save_dir, "final_model.pt")
    save_checkpoint(model, optimizer, config["epochs"]-1, {'psnr': psnr, 'ssim': ssim}, final_model_path)

    # 保存训练曲线和PSNR历史
    loss_curve_path = os.path.join(result_dir, "loss_curve.png")
    plot_loss_curve(train_loss_history, loss_curve_path)

    np.savez(
        os.path.join(config['result_dir'], "train_psnr_history.npz"),
        train_psnr_history=train_psnr_history
    )


if __name__ == "__main__":
    main()
