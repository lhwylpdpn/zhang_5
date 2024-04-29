import cv2
import numpy as np

# 加载图片
image = cv2.imread('../test.jpg', 0)

# 对图片进行阈值处理
_, thresh = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY_INV)
print(thresh)
# 寻找轮廓
contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

for contour in contours:
    # 获取包围轮廓的矩形
    x, y, w, h = cv2.boundingRect(contour)

    # 绘制每个网格单元周围的矩形并将它们保存为图片
    if w > 20 and h > 20:  # 根据你的图片调整这个条件
        cropped_grid_cell = image[y:y + h, x:x + w]
        cv2.imwrite(f'grid_cell_{x}_{y}.jpg', cropped_grid_cell)