import cv2
import numpy as np

# 加载图片
image = cv2.imread('../test.jpg', 0)

# 对图片进行阈值处理
_, thresh = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY_INV)
line_image = np.zeros_like(image)

# 使用Hough变换检测直线
lines = cv2.HoughLinesP(thresh, 1, np.pi/180, 150, minLineLength=100, maxLineGap=15)
# 绘制直线
for line in lines:
    x1, y1, x2, y2 = line[0]
    cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 0), 2)

# 显示包含直线的图像
cv2.imshow('lines', line_image)
cv2.waitKey(0)

# # 计算交点
# cross_points = []
# for i in range(len(lines)):
#     for j in range(i+1, len(lines)):
#         line1 = lines[i][0]
#         line2 = lines[j][0]
#         a1 = line1[3] - line1[1]
#         b1 = line1[0] - line1[2]
#         c1 = a1*line1[0] + b1*line1[1]
#         a2 = line2[3] - line2[1]
#         b2 = line2[0] - line2[2]
#         c2 = a2*line2[0] + b2*line2[1]
#         det = a1*b2 - a2*b1
#         if det != 0: # lines are not parallel
#             x = (b2*c1 - b1*c2) / det
#             y = (a1*c2 - a2*c1) / det
#             cross_points.append((x, y))
#
# # 根据交点切分图像
# cross_points = sorted(cross_points, key=lambda x: (x[1], x[0])) # sort by y, then by x
# for i in range(0, len(cross_points)-1):
#     for j in range(i+1, len(cross_points)):
#         x1, y1 = cross_points[i]
#         x2, y2 = cross_points[j]
#         if abs(y1-y2) < 10: # adjust this condition according to your image
#             cropped_grid_cell = image[int(y1):int(y2), int(x1):int(x2)]
#             cv2.imwrite(f'..\\temp\\grid_cell_{x1}_{y1}.jpg', cropped_grid_cell)
