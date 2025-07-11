# 训练相关文件：包含训练循环、评估指标计算和可视化函数
# 主要功能：
# 1. 预测结果可视化
# 2. 图像质量评估（PSNR, SSIM, NSE）
# 3. 训练循环实现

import torch
import numpy as np
import matplotlib.pyplot as plt

from torchmetrics.functional import peak_signal_noise_ratio
from skimage.metrics import structural_similarity as ssim_metric

def vis_pre(pred_img_complex):
    """可视化预测结果的统计信息
    
    Args:
        pred_img_complex: 预测的复数图像
    """
    print(f"Predicted image shape: {pred_img_complex.shape}")

    # 计算实部、虚部和幅度
    real_part = np.real(pred_img_complex)
    imag_part = np.imag(pred_img_complex)
    magnitude = np.abs(pred_img_complex)

    # 打印统计信息
    print("Real part stats: min: {:.4f}, max: {:.4f}, mean: {:.4f}, std: {:.4f}".format(
        real_part.min(), real_part.max(), real_part.mean(), real_part.std()))
    print("Imag part stats: min: {:.4f}, max: {:.4f}, mean: {:.4f}, std: {:.4f}".format(
        imag_part.min(), imag_part.max(), imag_part.mean(), imag_part.std()))
    print("Magnitude stats: min: {:.4f}, max: {:.4f}, mean: {:.4f}, std: {:.4f}".format(
        magnitude.min(), magnitude.max(), magnitude.mean(), magnitude.std()))

    # 创建网格坐标
    rows, cols = pred_img_complex.shape
    y_indices, x_indices = np.indices((rows, cols))

    # 展平数据
    x_flat = x_indices.flatten()
    y_flat = y_indices.flatten()
    real_flat = real_part.flatten()
    imag_flat = imag_part.flatten()
    mag_flat = magnitude.flatten()

    # 可视化实部
    plt.figure(figsize=(8, 6))
    sc = plt.scatter(x_flat, y_flat, c=real_flat, cmap='viridis', marker='o', s=10)
    plt.title('Predicted Image - Real Part')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.gca().invert_yaxis()
    plt.colorbar(sc)
    plt.savefig("Real_pred.png")

    # 可视化虚部
    plt.figure(figsize=(8, 6))
    sc = plt.scatter(x_flat, y_flat, c=imag_flat, cmap='viridis', marker='o', s=10)
    plt.title('Predicted Image - Imaginary Part')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.gca().invert_yaxis()
    plt.colorbar(sc)
    plt.savefig("Imag_pred.png")

    # 可视化幅度
    plt.figure(figsize=(8, 6))
    sc = plt.scatter(x_flat, y_flat, c=mag_flat, cmap='viridis', marker='o', s=10)
    plt.title('Predicted Image - Magnitude')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.gca().invert_yaxis()
    plt.colorbar(sc)
    plt.savefig("Mag_pred.png")

def normalize01(img):
    """将图像归一化到[0,1]范围
    
    Args:
        img: 输入图像
    
    Returns:
        归一化后的图像
    """
    if len(img.shape) == 3:
        nimg = len(img)
    else:
        nimg = 1
        r, c = img.shape
        img = np.reshape(img, (nimg, r, c))
    img2 = np.empty(img.shape, dtype=img.dtype)
    for i in range(nimg):
        img2[i]=(img[i]-img[i].min())/(img[i].max()-img[i].min())
    return np.squeeze(img2).astype(img.dtype)

def normalize02(img):
    """将图像归一化到[0,1]范围的另一种实现
    
    Args:
        img: 输入图像（numpy数组或PyTorch张量）
    
    Returns:
        归一化后的图像
    """
    if not isinstance(img, np.ndarray):
        try:
            img = img.cpu().numpy()
        except AttributeError:
            img = np.array(img)

    if len(img.shape) == 3:
        nimg = img.shape[0]
    else:
        nimg = 1
        r, c = img.shape
        img = np.reshape(img, (nimg, r, c))

    img2 = np.empty(img.shape, dtype=np.float32)

    for i in range(nimg):
        min_val = img[i].min()
        max_val = img[i].max()
        if max_val > min_val:
            img2[i] = (img[i] - min_val) / (max_val - min_val)
        else:
            img2[i] = 0.0

    return np.squeeze(img2)

def normalize_complex_to_range(x, new_min=-1, new_max=1, eps=1e-8):
    """将复数值归一化到指定范围
    
    Args:
        x: 输入的复数张量
        new_min: 目标范围的最小值
        new_max: 目标范围的最大值
        eps: 防止除零的小常数
    
    Returns:
        归一化后的复数张量
    """
    x_real = x.real
    x_imag = x.imag

    real_min = x_real.min()
    real_max = x_real.max()
    imag_min = x_imag.min()
    imag_max = x_imag.max()

    # 分别归一化实部和虚部
    norm_real = (x_real - real_min) / (real_max - real_min + eps) * (new_max - new_min) + new_min
    norm_imag = (x_imag - imag_min) / (imag_max - imag_min + eps) * (new_max - new_min) + new_min

    norm_complex = torch.complex(norm_real, norm_imag)
    return norm_complex

def final_output_image(pred_kspace, gt_kspace, mask):
    """生成最终的输出图像
    
    将预测的K空间数据与真实K空间数据结合，生成最终图像
    
    Args:
        pred_kspace: 预测的K空间数据
        gt_kspace: 真实的K空间数据
        mask: 采样掩模
    
    Returns:
        最终重建的图像
    """
    # 组合预测和真实的K空间数据
    final_kspace = pred_kspace * torch.abs(1 - mask) + gt_kspace * mask
    # 进行逆傅里叶变换
    final_image = torch.fft.ifft2(final_kspace)
    # 转换为numpy数组
    final_image_np = torch.abs(final_image).detach().cpu().numpy()
    return final_image_np

def compute_psnr(img1, img2):
    """计算峰值信噪比（PSNR）
    
    Args:
        img1, img2: 待比较的两个图像
    
    Returns:
        PSNR值
    """
    if isinstance(img1, np.ndarray):
        img1 = torch.from_numpy(img1).float()
    if isinstance(img2, np.ndarray):
        img2 = torch.from_numpy(img2).float()
    return peak_signal_noise_ratio(img1, img2, data_range=1.0)

def compute_ssim(img1, img2):
    """计算结构相似性（SSIM）
    
    Args:
        img1, img2: 待比较的两个图像
    
    Returns:
        SSIM值
    """
    return ssim_metric(img1, img2, data_range=img2.max() - img2.min())

def compute_nse(img1, img2):
    """计算归一化平方误差（NSE）
    
    Args:
        img1, img2: 待比较的两个图像
    
    Returns:
        NSE值
    """
    numerator = np.sum((img1 - img2) ** 2)
    denominator = np.sum(img2 ** 2)
    return numerator / denominator

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

def train_epoch_image(model, dataloader, optimizer, device, supervision_mode="image", lambda_tv=1e-5):
    """训练一个epoch
    
    Args:
        model: 神经网络模型
        dataloader: 数据加载器
        optimizer: 优化器
        device: 计算设备
        supervision_mode: 监督模式
        lambda_tv: 总变差正则化系数
    
    Returns:
        loss: 平均损失值
        psnr: 平均PSNR值
        ssim: 平均SSIM值
        nse: 平均NSE值
    """
    model.train()
    total_loss, total_psnr, total_ssim, total_nse = 0, 0, 0, 0
    count = 0
    
    for batch in dataloader:
        # 获取输入数据
        coords = batch['coords'][0].to(device)
        gt_img = batch['gt_img'][0].to(device)
        mask = batch['mask'][0].to(device)
        H, W = gt_img.shape

        # 前向传播
        pred_flat = model(coords)
        pred_img_complex = get_image_from_prediction(pred_flat, H, W)

        if supervision_mode == "kspace_csm":
            # 获取线圈灵敏度图
            gt_csm = batch["gt_csm"].to(device)
            pred_img_complex_expanded = pred_img_complex.unsqueeze(0).unsqueeze(0).repeat(1, 12, 1, 1)

            # 计算背景惩罚
            mask_real = torch.where(gt_csm.real == 0,
                                    torch.tensor(1.0, device=gt_csm.device),
                                    torch.tensor(0.0, device=gt_csm.device))
            mask_imag = torch.where(gt_csm.imag == 0,
                                    torch.tensor(1.0, device=gt_csm.device),
                                    torch.tensor(0.0, device=gt_csm.device))

            penalty_real = pred_img_complex.real * mask_real
            penalty_imag = pred_img_complex.imag * mask_imag

            background_penalty_loss = (penalty_real ** 2).sum() + (penalty_imag ** 2).sum()

            # 计算线圈图像
            csm_pred_img_complex = pred_img_complex_expanded * gt_csm

            # 计算K空间损失
            pred_kspace = torch.fft.fft2(csm_pred_img_complex)
            gt_kspace = batch["gt_loss_csm_kspace"].to(device)
            pred_real = torch.view_as_real(pred_kspace)
            gt_real = torch.view_as_real(gt_kspace)
            diff = pred_real - gt_real
            error = (diff ** 2).sum(dim=-1)

            mask = batch["mask"].to(device)
            if mask.ndim == 2:
                mask = mask.unsqueeze(0)
            mse_loss_k = (error * mask).sum() / (mask.sum() + 1e-6)

            # 总损失
            mse_loss = 1 * mse_loss_k + 0.01 * background_penalty_loss
        else:
            raise ValueError("Unsupport Supervision_mode")

        # 计算总变差损失
        mag = torch.abs(pred_img_complex)
        if mag.dim() > 2:
            mag = mag.squeeze(0)
        tv_h = torch.mean(torch.abs(mag[:, 1:] - mag[:, :-1]))
        tv_v = torch.mean(torch.abs(mag[1:, :] - mag[:-1, :]))
        tv_loss = tv_h + tv_v

        # 计算总损失
        lambda_tv_tensor = torch.tensor(float(lambda_tv), device=device, dtype=mse_loss.dtype)
        loss = mse_loss + lambda_tv_tensor * tv_loss

        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # 计算评估指标
        total_loss += loss.item()
        pred_img_np = torch.abs(pred_img_complex).detach().cpu().numpy()
        gt_img_np = torch.abs(gt_img).detach().cpu().numpy()

        total_psnr += compute_psnr(pred_img_np, gt_img_np)
        total_ssim += compute_ssim(pred_img_np, gt_img_np)
        total_nse += compute_nse(pred_img_np, gt_img_np)

        count += 1

    # 返回平均指标
    return total_loss / count, total_psnr / count, total_ssim / count, total_nse / count

