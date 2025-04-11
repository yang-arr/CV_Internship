# 模型定义文件：实现了基于SIREN的隐式神经网络模型
# 主要包含以下组件：
# 1. ReLU激活层：标准的ReLU激活函数层
# 2. Sine激活层：SIREN中使用的正弦激活函数层
# 3. 傅里叶特征映射：将低维坐标映射到高维空间
# 4. 专家MLP：多层感知机网络
# 5. 完整模型：组合以上组件的最终模型

import math
import torch
import numpy as np
import torch.nn as nn


class ReLUActivationLayer(nn.Module):
    """ReLU激活层
    
    参数:
        in_features (int): 输入特征维度
        out_features (int): 输出特征维度
        is_first (bool): 是否是第一层（影响初始化方式）
        omega_0 (float): 频率参数（对ReLU不起作用）
        sigma (float): 初始化的标准差
    """
    def __init__(self, in_features, out_features, is_first=False, omega_0=20, sigma=1):
        super(ReLUActivationLayer, self).__init__()
        self.linear = nn.Linear(in_features, out_features)
        self.init_weights()

    def init_weights(self):
        """初始化网络权重
        使用kaiming初始化方法，适用于ReLU激活函数
        """
        nn.init.kaiming_normal_(self.linear.weight, nonlinearity='relu')
        if self.linear.bias is not None:
            nn.init.constant_(self.linear.bias, 0.0)

    # FMLP对ReLU层的初始化 适用于FourierFeature sigma是一个可变频率 作为超参数调制
    # def init_weights(self):
    #    with torch.no_gard():
    #        self.linear.weight.normal_(std=self.sigma)
    #        if self.linear.bias is not None:
    #            self.linear.bias.normal_(std=1e-6)

    def forward(self, x):
        """前向传播
        Args:
            x: 输入张量
        Returns:
            应用ReLU激活函数后的结果
        """
        return torch.relu(self.linear(x))


class SineActivationLayer(nn.Module):
    """正弦激活层（SIREN的核心组件）
    
    参数:
        in_features (int): 输入特征维度
        out_features (int): 输出特征维度
        is_first (bool): 是否是第一层（影响初始化方式）
        omega_0 (float): 正弦函数的频率参数
    """
    def __init__(self, in_features, out_features, is_first=False, omega_0=30):
        super(SineActivationLayer, self).__init__()
        self.linear = nn.Linear(in_features, out_features)
        self.omega_0 = omega_0
        self.is_first = is_first
        self.init_weights(in_features)

    def init_weights(self, in_features):
        """特殊的权重初始化方法
        
        第一层和其他层使用不同的初始化范围，这是SIREN的关键
        """
        with torch.no_grad():
            if self.is_first:
                # 第一层使用均匀分布初始化
                self.linear.weight.uniform_(-1 / in_features, 1 / in_features)
            else:
                # 其他层使用更大范围的均匀分布
                self.linear.weight.uniform_(-np.sqrt(6 / in_features), np.sqrt(6 / in_features))

    def forward(self, x):
        """前向传播
        Args:
            x: 输入张量
        Returns:
            应用正弦激活函数后的结果
        """
        if self.is_first:
            # 第一层需要乘以频率参数
            return torch.sin(self.omega_0 * self.linear(x))
        else:
            return torch.sin(self.linear(x))


def get_activation_layer(in_features, out_features, activation, is_first, omega_0):
    """创建激活层的工厂函数
    
    Args:
        in_features: 输入特征维度
        out_features: 输出特征维度
        activation: 激活函数类型 ('relu' 或 'sine')
        is_first: 是否是第一层
        omega_0: 频率参数
    
    Returns:
        相应的激活层实例
    """
    if activation.lower() == "relu":
        return ReLUActivationLayer(in_features, out_features, is_first=is_first, omega_0=omega_0)
    elif activation.lower() == "sine":
        return SineActivationLayer(in_features, out_features, is_first=is_first, omega_0=omega_0)
    else:
        raise ValueError("Unsupported activation: " + activation)


class FourierFeatureMap(nn.Module):
    """傅里叶特征映射层
    
    将低维坐标映射到高维空间，使网络更容易学习高频函数
    
    参数:
        in_features: 输入特征维度（通常是2，对应x,y坐标）
        out_features: 输出特征维度（必须是偶数）
        coordinate_scales: 坐标缩放因子
    """
    def __init__(self, in_features, out_features, coordinate_scales):
        super(FourierFeatureMap, self).__init__()
        assert out_features % 2 == 0, "Fourier Features not even number!"
        self.num_freq = out_features // 2
        self.out_features = out_features
        # 坐标缩放参数
        self.coordinate_scales = nn.Parameter(
            torch.tensor(coordinate_scales, dtype=torch.float32).unsqueeze(0),
            requires_grad=False
        )
        # 随机频率矩阵
        self.B = torch.normal(0, 3, (in_features, self.num_freq)) * 10
        self.B = nn.Parameter(self.B, requires_grad=False)

    def forward(self, x):
        """前向传播
        
        Args:
            x: 形状为[batch_size, 2]的输入坐标
        
        Returns:
            形状为[batch_size, out_features]的傅里叶特征
        """
        # 应用坐标缩放
        scaled = self.coordinate_scales * x
        # 计算投影
        proj = scaled @ self.B
        # 生成正弦和余弦特征
        sin_feat = np.sqrt(2) * torch.sin(proj)
        cos_feat = np.sqrt(2) * torch.cos(proj)
        # 拼接特征
        return torch.cat((sin_feat, cos_feat), dim=-1)


class ExpertMLP(nn.Module):
    """多层感知机网络
    
    参数:
        in_features: 输入特征维度
        hidden_features: 隐藏层特征维度
        hidden_layers: 隐藏层数量
        out_features: 输出特征维度
        omega_0: SIREN的频率参数
        activation: 激活函数类型
    """
    def __init__(self, in_features, hidden_features, hidden_layers, out_features, omega_0, activation):
        super(ExpertMLP, self).__init__()
        layers = []
        # 添加第一层（特殊初始化）
        first_layer = get_activation_layer(in_features, hidden_features, activation, is_first=True, omega_0=omega_0)
        layers.append(first_layer)
        # 添加隐藏层
        for i in range(hidden_layers):
            layer = get_activation_layer(hidden_features, hidden_features, activation, is_first=False, omega_0=omega_0)
            layers.append(layer)
        # 添加输出层
        final_layer = nn.Linear(hidden_features, out_features)
        layers.append(final_layer)
        # 构建网络
        self.mlp = nn.Sequential(*layers)

    def forward(self, x):
        """前向传播"""
        return self.mlp(x)


class Fullmodel(nn.Module):
    """完整的MRI重建模型
    
    组合了傅里叶特征映射和MLP网络
    
    参数:
        encoding_mode: 编码方式（目前只支持"fourier"）
        in_features: 输入特征维度（通常是2）
        out_features: 傅里叶特征维度
        coordinate_scales: 坐标缩放因子
        mlp_hidden_features: MLP隐藏层的特征数
        mlp_hidden_layers: MLP的隐藏层数量
        omega_0: SIREN的频率参数
        activation: 激活函数类型
    """
    def __init__(self,
                 encoding_mode,
                 in_features, out_features, coordinate_scales,
                 mlp_hidden_features, mlp_hidden_layers,
                 omega_0, activation):
        super(Fullmodel, self).__init__()
        self.encoding_mode = encoding_mode.lower()
        # 创建编码器
        if self.encoding_mode == "fourier":
            self.encoder = FourierFeatureMap(
                in_features, out_features, coordinate_scales)
            encoder_output_dim = out_features
        else:
            raise ValueError("Unsupported encoding_mode: " + encoding_mode)
        # 创建MLP网络
        self.net = ExpertMLP(encoder_output_dim, mlp_hidden_features, 
                            mlp_hidden_layers, 2, omega_0, activation)

    def forward(self, x):
        """前向传播
        
        Args:
            x: 形状为[batch_size, 2]的输入坐标
        
        Returns:
            形状为[batch_size, 2]的输出，表示每个坐标点的复数值（实部和虚部）
        """
        # 编码输入坐标
        encoded = self.encoder(x)
        # 通过MLP网络处理
        out = self.net(encoded)
        return out

