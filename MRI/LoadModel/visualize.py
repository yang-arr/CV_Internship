# 可视化相关文件：包含模型预测结果的可视化和保存功能
# 主要功能：
# 1. 预测结果图像转换
# 2. 训练过程中的结果保存
# 3. 最佳结果保存
# 4. 损失曲线绘制

import os
import torch
import numpy as np

import matplotlib.pyplot as plt


def get_image_from_prediction(pred_flat, H, W):
    """从预测结果重构图像
    
    Args:
        pred_flat: 预测的平坦张量
        H, W: 目标图像的高度和宽度
    
    Returns:
        重构的复数图像
    """
    img_complex = torch.view_as_complex(pred_flat.view(H, W, 2))
    return img_complex


def save_epoch_results_as_png(model, sample, device, epoch, save_dir, supervision_mode="image"):
    """保存每个epoch的训练结果
    
    Args:
        model: 训练好的模型
        sample: 数据样本
        device: 计算设备
        epoch: 当前epoch
        save_dir: 保存目录
        supervision_mode: 监督模式
    """
    # 创建保存目录
    epoch_dir = os.path.join(save_dir, f"epoch_{epoch + 1}")
    os.makedirs(epoch_dir, exist_ok=True)
    
    # 模型设置为评估模式
    model.eval()
    coords = sample['coords'].to(device)
    
    # 进行预测
    with torch.no_grad():
        pred_flat = model(coords)
    
    H, W = sample['gt_img'].shape
    
    # 根据不同的监督模式处理预测结果
    if supervision_mode in ['kspace', 'kspace_csm', 'image']:
        # 获取预测的复数图像
        pred_img_complex = get_image_from_prediction(pred_flat, H, W)
        pred_real = pred_img_complex.real.detach().cpu().numpy()
        pred_imag = pred_img_complex.imag.detach().cpu().numpy()
        pred_mag = torch.abs(pred_img_complex).detach().cpu().numpy()

        # 保存实部、虚部和幅度图像
        plt.imsave(os.path.join(epoch_dir, "pred_real.png"), pred_real, cmap="gray")
        plt.imsave(os.path.join(epoch_dir, "pred_imag.png"), pred_imag, cmap="gray")
        plt.imsave(os.path.join(epoch_dir, "pred_mag.png"), pred_mag, cmap="gray")

        print(f"Saved epoch {epoch + 1} predictions in {epoch_dir}")
    elif supervision_mode in ['pred_full_kspae', 'pred_loss_kspace']:
        # 对K空间数据进行逆傅里叶变换
        fake_pred_img_complex = get_image_from_prediction(pred_flat, H, W)
        pred_img_complex = torch.fft.ifft2(fake_pred_img_complex)
        pred_real = pred_img_complex.real.detach().cpu().numpy()
        pred_imag = pred_img_complex.imag.detach().cpu().numpy()
        pred_mag = torch.abs(pred_img_complex).detach().cpu().numpy()

        # 保存结果
        plt.imsave(os.path.join(epoch_dir, "pred_real.png"), pred_real, cmap="gray")
        plt.imsave(os.path.join(epoch_dir, "pred_imag.png"), pred_imag, cmap="gray")
        plt.imsave(os.path.join(epoch_dir, "pred_mag.png"), pred_mag, cmap="gray")

        print(f"Saved epoch {epoch + 1} predictions in {epoch_dir}")
    else:
        raise ValueError("Unsupport Prediction_mode")


def save_best_image(model, sample, device, psnr, ssim, save_dir, supervision_mode="image"):
    """保存最佳训练结果
    
    Args:
        model: 训练好的模型
        sample: 数据样本
        device: 计算设备
        psnr: 峰值信噪比
        ssim: 结构相似性
        save_dir: 保存目录
        supervision_mode: 监督模式
    """
    os.makedirs(save_dir, exist_ok=True)
    model.eval()
    coords = sample['coords'].to(device)
    
    # 进行预测
    with torch.no_grad():
        pred_flat = model(coords)
    
    H, W = sample['gt_img'].shape
    
    # 根据不同的监督模式处理预测结果
    if supervision_mode in ['kspace', 'kspace_csm', 'image']:
        # 获取预测的复数图像
        pred_img_complex = get_image_from_prediction(pred_flat, H, W)
        pred_real = pred_img_complex.real.detach().cpu().numpy()
        pred_imag = pred_img_complex.imag.detach().cpu().numpy()
        pred_mag = torch.abs(pred_img_complex).detach().cpu().numpy()

        # 保存最佳结果
        best_dir = save_dir
        plt.imsave(os.path.join(best_dir, "best_pred_real.png"), pred_real, cmap="gray")
        plt.imsave(os.path.join(best_dir, "best_pred_imag.png"), pred_imag, cmap="gray")
        plt.imsave(os.path.join(best_dir, "best_pred_mag.png"), pred_mag, cmap="gray")

    elif supervision_mode in ['pred_full_kspae', 'pred_loss_kspace']:
        # 对K空间数据进行逆傅里叶变换
        fake_pred_img_complex = get_image_from_prediction(pred_flat, H, W)
        pred_img_complex = torch.fft.ifft2(fake_pred_img_complex)
        pred_real = pred_img_complex.real.detach().cpu().numpy()
        pred_imag = pred_img_complex.imag.detach().cpu().numpy()
        pred_mag = torch.abs(pred_img_complex).detach().cpu().numpy()

        # 保存最佳结果
        best_dir = save_dir
        plt.imsave(os.path.join(best_dir, "pred_real.png"), pred_real, cmap="gray")
        plt.imsave(os.path.join(best_dir, "pred_imag.png"), pred_imag, cmap="gray")
        plt.imsave(os.path.join(best_dir, "pred_mag.png"), pred_mag, cmap="gray")

    # 保存评估指标
    metrics_filepath = os.path.join(best_dir, "best_metrics.txt")
    with open(metrics_filepath, "w") as f:
        f.write(f"PSNR: {psnr:.2f}\nSSIM: {ssim:.4f}\n")
    #print(f"Saved best prediction images in {best_dir}")



def plot_loss_curve(train_loss_history, loss_curve_path):
    """绘制训练损失曲线
    
    Args:
        train_loss_history: 训练损失历史记录
        loss_curve_path: 曲线保存路径
    """
    plt.figure()
    plt.plot(range(1, len(train_loss_history) + 1), train_loss_history, label="Train Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Loss Curve")
    plt.legend()
    os.makedirs(os.path.dirname(loss_curve_path), exist_ok=True)
    plt.savefig(loss_curve_path)
    plt.close()
    print(f"Saved loss curve to {loss_curve_path}")