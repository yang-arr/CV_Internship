import h5py
import os
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

def normalize01(img):
    """
    将图像归一化到[0,1]范围
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

def save_complex_image(data, save_path, index, prefix):
    """
    保存复数图像的实部、虚部和幅度图
    """
    # 确保保存目录存在
    os.makedirs(save_path, exist_ok=True)
    
    # 获取实部、虚部和幅度
    magnitude = np.abs(data)
    real_part = np.real(data)
    imag_part = np.imag(data)
    
    # 归一化
    magnitude_norm = normalize01(magnitude)
    real_norm = normalize01(real_part)
    imag_norm = normalize01(imag_part)
    
    # 保存幅度图
    plt.imsave(
        os.path.join(save_path, f"{prefix}_magnitude_{index}.png"),
        magnitude_norm,
        cmap='gray'
    )
    
    # 保存实部
    plt.imsave(
        os.path.join(save_path, f"{prefix}_real_{index}.png"),
        real_norm,
        cmap='gray'
    )
    
    # 保存虚部
    plt.imsave(
        os.path.join(save_path, f"{prefix}_imag_{index}.png"),
        imag_norm,
        cmap='gray'
    )

def convert_dataset(file_path):
    """
    转换h5数据集为图片文件
    """
    print("开始读取数据集...")
    with h5py.File(file_path, 'r') as data:
        # 获取数据
        org_data = data['trnOrg'][:]      # 原始图像
        mask_data = data['trnMask'][:]    # 掩模
        csm_data = data['trnCsm'][:]      # 线圈灵敏度图
        
        num_samples = len(org_data)
        print(f"总共有 {num_samples} 个样本")
        
        # 创建保存目录
        base_dir = "data/converted_dataset"
        original_dir = os.path.join(base_dir, "original")
        kspace_dir = os.path.join(base_dir, "kspace")
        mask_dir = os.path.join(base_dir, "mask")
        csm_dir = os.path.join(base_dir, "csm")
        
        os.makedirs(original_dir, exist_ok=True)
        os.makedirs(kspace_dir, exist_ok=True)
        os.makedirs(mask_dir, exist_ok=True)
        os.makedirs(csm_dir, exist_ok=True)
        
        print("开始转换数据...")
        for i in tqdm(range(num_samples)):
            # 保存原始图像
            save_complex_image(org_data[i], original_dir, i, "original")
            
            # 计算并保存K空间数据
            kspace = np.fft.fft2(org_data[i])
            save_complex_image(kspace, kspace_dir, i, "kspace")
            
            # 保存掩模
            plt.imsave(
                os.path.join(mask_dir, f"mask_{i}.png"),
                mask_data[i],
                cmap='gray'
            )
            
            # 保存每个通道的线圈灵敏度图
            for j in range(csm_data.shape[1]):
                save_complex_image(
                    csm_data[i, j],
                    os.path.join(csm_dir, f"channel_{j}"),
                    i,
                    f"csm_ch{j}"
                )
        
        print("数据转换完成！")
        print(f"文件已保存到 {base_dir} 目录下")
        print("目录结构：")
        print(f"- {base_dir}/")
        print("  ├── original/  (原始图像)")
        print("  ├── kspace/   (K空间数据)")
        print("  ├── mask/     (采样掩模)")
        print("  └── csm/      (线圈灵敏度图)")

if __name__ == "__main__":
    # 替换为你的数据集路径
    dataset_path = "data/dataset.hdf5"  # 请修改为实际的数据集路径
    convert_dataset(dataset_path) 