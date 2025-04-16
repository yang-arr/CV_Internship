#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
生成"图片未找到"的PNG图片
"""

from PIL import Image, ImageDraw, ImageFont
import os

# 创建一个空白图像
img = Image.new('RGB', (200, 200), color=(242, 242, 242))
draw = ImageDraw.Draw(img)

# 画一个圆圈和交叉线
draw.ellipse((50, 50, 150, 150), outline=(153, 153, 153), width=5)
draw.line((75, 65, 125, 135), fill=(153, 153, 153), width=5)
draw.line((125, 65, 75, 135), fill=(153, 153, 153), width=5)

# 添加文本
try:
    # 尝试使用Arial字体，如果不可用，使用默认字体
    font = ImageFont.truetype("arial.ttf", 14)
except:
    font = ImageFont.load_default()

draw.text((100, 170), "图片未找到", fill=(102, 102, 102), font=font, anchor="ms")

# 保存图像
script_dir = os.path.dirname(os.path.abspath(__file__))
img.save(os.path.join(script_dir, "image-not-found.png"))

print("图片已生成：image-not-found.png")