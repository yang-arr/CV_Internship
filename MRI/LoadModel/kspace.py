import os
import h5py
import torch
import numpy as np
import matplotlib.pyplot as plt


def normalize01(img):
    """
    将图像归一化到 [0, 1] 区间
    """
    if not isinstance(img, np.ndarray):
        try:
            img = img.cpu().numpy()
        except AttributeError:
            img = np.array(img)
    # 如果图像是二维的，则扩展成 (1, H, W)
    if len(img.shape) == 2:
        img = np.expand_dims(img, axis=0)
    nimg = img.shape[0]
    img_norm = np.empty(img.shape, dtype=np.float32)
    for i in range(nimg):
        min_val = img[i].min()
        max_val = img[i].max()
        if max_val > min_val:
            img_norm[i] = (img[i] - min_val) / (max_val - min_val)
        else:
            img_norm[i] = 0.0
    return np.squeeze(img_norm)


def load_dataset(file_path):
    """
    打开 HDF5 数据文件，返回原始图像和采样掩码
    """
    with h5py.File(file_path, 'r') as f:
        # 原始图像：形状 (N, H, W)
        trnOrg = f['trnOrg'][:]
        # 采样掩码：形状 (N, H, W)，1 表示采样到的 k-space 点，0 表示未采样
        trnMask = f['trnMask'][:]
    return trnOrg, trnMask


def zero_filled_reconstruction(org_img, mask):
    """
    对单幅原始图像和对应的采样掩码，计算欠采样（零填充）重建图像
    """
    # 将原始图像转换为 PyTorch 张量
    org_tensor = torch.from_numpy(org_img)

    # 计算完整的 k-space 数据（二维 FFT）
    full_kspace = torch.fft.fft2(org_tensor)

    # 利用采样掩码进行欠采样，即未采样位置置零
    # 注意：确保掩码为同类型张量
    mask_tensor = torch.from_numpy(mask).to(full_kspace.dtype)
    masked_kspace = full_kspace * mask_tensor

    # 通过逆傅里叶变换得到零填充重建图像
    zero_filled_image = torch.fft.ifft2(masked_kspace)

    # 取复数结果的模值用于显示
    zero_filled_magnitude = torch.abs(zero_filled_image)
    return zero_filled_magnitude.numpy()


def save_and_display_zero_filled_images(file_path, output_folder, sample_indices):
    """
    加载数据集，针对指定的样本索引计算欠采样（零填充）重建图像，
    将结果保存到 output_folder 中，同时显示图像
    """
    # 创建输出文件夹（如果不存在的话）
    os.makedirs(output_folder, exist_ok=True)

    # 加载原始图像和采样掩码
    trnOrg, trnMask = load_dataset(file_path)

    for idx in sample_indices:
        # 读取第 idx 幅图像和对应的掩码
        org_img = trnOrg[idx]  # shape: (H, W)
        mask = trnMask[idx]  # shape: (H, W)

        # 计算零填充重建图像
        zero_filled = zero_filled_reconstruction(org_img, mask)
        # 归一化用于显示和保存
        zero_filled_norm = normalize01(zero_filled)

        # 构造保存文件名
        save_path = os.path.join(output_folder, f"zero_filled_{idx}.png")

        # 使用 Matplotlib 保存图像
        plt.figure(figsize=(8, 6))
        plt.imshow(zero_filled_norm, cmap='gray')
        plt.axis('off')
        plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
        plt.close()
        print(f"保存图像：{save_path}")

        # 可选：显示图像
        plt.figure(figsize=(8, 6))
        plt.imshow(zero_filled_norm, cmap='gray')
        plt.title(f"Zero-filled Reconstruction (Index {idx})")
        plt.axis('off')
        # plt.show()


if __name__ == '__main__':
    # 请将 file_path 替换为你的 HDF5 数据文件路径
    file_path = "data/dataset.hdf5"
    # 指定保存图像的文件夹路径
    output_folder = "output_zero_filled_images"
    # 指定要显示和保存的样本索引列表，比如 [0, 1, 2]
    sample_indices = [1, 91,181,271,359]

    save_and_display_zero_filled_images(file_path, output_folder, sample_indices)