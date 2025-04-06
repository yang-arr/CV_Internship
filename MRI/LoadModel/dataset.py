# 数据集处理文件：负责MRI数据的加载和预处理
# 主要功能：
# 1. 数据归一化
# 2. 数据可视化
# 3. 数据集类定义（包含原始图像、掩模、线圈灵敏度图等）

import h5py
import torch
import numpy as np
import matplotlib.pyplot as plt

from torch.utils.data import Dataset

def normalize01(img):
    """将图像归一化到[0,1]范围
    
    Args:
        img: 输入图像，可以是numpy数组或PyTorch张量
    
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

def vis_data(sample):
    """可视化复数数据
    
    将复数数据的实部、虚部和幅度分别可视化
    
    Args:
        sample: 复数数据样本
    """
    # 获取实部、虚部和幅度
    real_part = np.real(sample)
    imag_part = np.imag(sample)
    magnitude = np.abs(sample)

    # 创建网格坐标
    rows, cols = real_part.shape
    y_indices, x_indices = np.indices((rows, cols))

    # 展平数据用于散点图
    x_flat = x_indices.flatten()
    y_flat = y_indices.flatten()
    real_flat = real_part.flatten()
    imag_flat = imag_part.flatten()
    mag_flat = magnitude.flatten()

    # 绘制实部
    plt.figure(figsize=(8, 6))
    sc = plt.scatter(x_flat, y_flat, c=real_flat, cmap='viridis', marker='o', s=10)
    plt.title(f'Sample - Real Part')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.gca().invert_yaxis()
    plt.colorbar(sc)
    plt.savefig("Real.png")

    # 绘制虚部
    plt.figure(figsize=(8, 6))
    sc = plt.scatter(x_flat, y_flat, c=imag_flat, cmap='viridis', marker='o', s=10)
    plt.title(f'Sample - Imaginary Part')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.gca().invert_yaxis()
    plt.colorbar(sc)
    plt.show()
    plt.savefig("Imag.png")

    # 绘制幅度
    plt.figure(figsize=(8, 6))
    sc = plt.scatter(x_flat, y_flat, c=mag_flat, cmap='viridis', marker='o', s=10)
    plt.title(f'Sample - Magnitude')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.gca().invert_yaxis()
    plt.colorbar(sc)
    plt.savefig("Mag.png")

class MRIDataset(Dataset):
    """MRI数据集类
    
    处理和加载MRI相关的所有数据，包括：
    - 原始图像
    - 采样掩模
    - 线圈灵敏度图
    - 坐标信息
    
    Args:
        file_path: h5文件路径
        split: 数据集划分（'train'或'test'）
    """
    def __init__(self, file_path, split='train'):
        super(MRIDataset, self).__init__()
        self.file_path = file_path
        self.split = split
        self.data = h5py.File(file_path, 'r')
        
        # 加载数据
        self.org_data = self.data['trnOrg'][:]      # 原始图像 (N, H, W)
        self.mask_data = self.data['trnMask'][:]    # 采样掩模 (N, H, W)
        self.csm_data = self.data['trnCsm'][:]      # 线圈灵敏度图 (N, C, H, W)
        
        # 获取数据维度
        self.num_samples = self.org_data[0]
        self.H = self.org_data.shape[1]  # 图像高度
        self.W = self.org_data.shape[2]  # 图像宽度
        self.C = self.csm_data.shape[1]  # 线圈数量

        # 生成归一化的坐标网格
        xs = np.linspace(-1, 1, self.W)
        ys = np.linspace(-1, 1, self.H)
        grid_y, grid_x = np.meshgrid(ys, xs, indexing='ij')
        coords = np.stack([grid_x, grid_y], axis=-1)
        self.coords = torch.tensor(coords, dtype=torch.float32).view(-1, 2)

    def __getitem__(self, idx):
        """获取单个数据样本
        
        Args:
            idx: 样本索引
        
        Returns:
            包含以下键的字典：
            - coords: 归一化坐标点
            - gt_full_kspace: 完整的K空间数据
            - gt_loss_kspace: 掩模后的K空间数据
            - gt_full_csm_kspace: 完整的线圈K空间数据
            - gt_loss_csm_kspace: 掩模后的线圈K空间数据
            - mask: 采样掩模
            - gt_img: 原始图像
            - gt_csm: 线圈灵敏度图
        """
        # 获取原始数据
        org_np = self.org_data[idx]
        mask_np = self.mask_data[idx]
        csm_np = self.csm_data[idx]

        # 转换为PyTorch张量
        org = torch.from_numpy(org_np)
        mask = torch.from_numpy(mask_np).float()
        csm = torch.from_numpy(csm_np).to(torch.complex64)

        # 处理线圈维度
        if org.ndim == 2:
            org_expand = org.unsqueeze(0).repeat(csm.shape[0], 1, 1)

        # 计算K空间数据
        full_kspace = torch.fft.fft2(org)
        masked_kspace = full_kspace * mask
        inverse_masked_kspace = full_kspace * (1 - mask)

        # 可视化K空间数据
        plt.imshow(normalize01(np.abs(full_kspace)), cmap=plt.cm.gray, clim=(0.0, 0.8))
        plt.axis('off')
        plt.show()
        plt.savefig('full_kspace.png', bbox_inches='tight', pad_inches=0)
        plt.close()

        plt.imshow(normalize01(np.abs(masked_kspace)), cmap=plt.cm.gray, clim=(0.0, 0.8))
        plt.axis('off')
        plt.show()
        plt.savefig('masked_kspace.png', bbox_inches='tight', pad_inches=0)
        plt.close()

        plt.imshow(normalize01(np.abs(inverse_masked_kspace)), cmap=plt.cm.gray, clim=(0.0, 0.8))
        plt.axis('off')
        plt.show()
        plt.savefig('inverse_masked_kspace.png', bbox_inches='tight', pad_inches=0)
        plt.close()

        # 计算线圈相关的数据
        csm_org = org_expand * csm
        full_csm_kspace = torch.fft.fft2(csm_org)

        # 处理掩模维度
        if mask.ndim == 2:
            mask = mask.unsqueeze(0).repeat(csm.shape[0], 1, 1)
        masked_csm_kspace = full_csm_kspace * mask

        # 返回数据字典
        sample = {
            'coords': self.coords,                    # 坐标点
            'gt_full_kspace': full_kspace,           # 完整K空间
            'gt_loss_kspace': masked_kspace,         # 掩模后K空间
            'gt_full_csm_kspace': full_csm_kspace,   # 完整线圈K空间
            'gt_loss_csm_kspace': masked_csm_kspace, # 掩模后线圈K空间
            'mask': mask,                            # 掩模
            'gt_img': org,                           # 原始图像
            'gt_csm': csm,                           # 线圈灵敏度图
        }
        return sample

    def __len__(self):
        """返回数据集大小"""
        return self.num_samples
