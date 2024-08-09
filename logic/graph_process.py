import time

import cv2
import numpy as np
import math
import pytesseract
from pytesseract import Output
from skimage.metrics import structural_similarity as ssim


# 加载图片

def test1():
    image = cv2.imread('../test4.jpg', 0)

    # 对图片进行阈值处理
    _, thresh = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY_INV)
    line_image = np.zeros_like(image)



    #条件1:距离边距多少以上的
    #条件2:长度最少多少
    #条件3：倾斜度多少以上

    edge_distance =30
    minLineLength=200
    slope_threshold = 0.03
    slope=0
    horizontal_lines = []
    vertical_lines = []



    # 使用Hough变换检测直线
    lines = cv2.HoughLinesP(thresh, 1, np.pi/180, 100, minLineLength=minLineLength, maxLineGap=10)
    # 绘制直线
    # 定义边缘距离


    lines_with_length=[]
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x1 > edge_distance and x1 < image.shape[1] - edge_distance and y1 > edge_distance and y1 < image.shape[0] - edge_distance and x2 > edge_distance and x2 < image.shape[1] - edge_distance and y2 > edge_distance and y2 < image.shape[0] - edge_distance:
            if x2 - x1 != 0:
                slope = (y2 - y1) / (x2 - x1)
            else:
                slope = float('inf')


            if abs(slope) < slope_threshold:
                length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                horizontal_lines.append((x1, y1, x2, y2, length))
            elif abs(slope) > 1 / slope_threshold:

                length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

                vertical_lines.append((x1, y1, x2, y2, length))

    horizontal_lines=sorted(horizontal_lines,key=lambda x:x[4],reverse=True)
    vertical_lines=sorted(vertical_lines,key=lambda x:x[4],reverse=True)

    for x1, y1, x2, y2,length in horizontal_lines:
        cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 0), 2)

    for x1, y1, x2, y2,length in vertical_lines:
        cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 0), 2)

    # # 显示包含直线的图像
    # cv2.imshow('lines', line_image)
    # cv2.waitKey(0)
    lines = cv2.HoughLinesP(thresh, 1, np.pi/180, 50, minLineLength=30, maxLineGap=10)

    # 计算交点
    cross_points = []
    for i in range(len(lines)):
        for j in range(i+1, len(lines)):
            line1 = lines[i][0]
            line2 = lines[j][0]
            a1 = line1[3] - line1[1]
            b1 = line1[0] - line1[2]
            c1 = a1*line1[0] + b1*line1[1]
            a2 = line2[3] - line2[1]
            b2 = line2[0] - line2[2]
            c2 = a2*line2[0] + b2*line2[1]
            det = a1*b2 - a2*b1
            if det != 0: # lines are not parallel
                x = (b2*c1 - b1*c2) / det
                y = (a1*c2 - a2*c1) / det
                cross_points.append((x, y))

    # 根据交点切分图像
    cross_points = sorted(cross_points, key=lambda x: (x[1], x[0])) # sort by y, then by x
    for i in range(0, len(cross_points)-1):
        for j in range(i+1, len(cross_points)):
            x1, y1 = cross_points[i]
            x2, y2 = cross_points[j]
            cv2.line(line_image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
    cv2.imshow('Result', line_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def test2():
    import cv2
    import numpy as np

    # 读取图像
    img = cv2.imread('../test4.jpg')

    # 转换为灰度图像
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 应用二值化
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    # 使用形态学操作连接字符
    kernel = np.ones((10, 10), np.uint8)
    connected_text = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # 找到轮廓
    contours, _ = cv2.findContours(connected_text, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # 遍历所有轮廓
    min_width = 0
    max_width = 10000
    min_height = 0
    max_height = 10000
    #清空文件夹..//tmp//
    import os
    for file in os.listdir('..//tmp//'):
        os.remove('..//tmp//'+file)
    for cnt in contours:
        # 计算轮廓的外接矩形


        # 切割图像
        x, y, w, h = cv2.boundingRect(cnt)

        margin = 0  # 设置边距
        roi = img[y + margin:y + h - margin, x + margin:x + w - margin]
        if min_width <= w <= max_width and min_height <= h <= max_height:
            cv2.imwrite(f'..//tmp//grid_cell_{x}_{y}___{w}_{h}.jpg', roi)


    # cv2.imshow('Result', img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()



def test3():
    import cv2
    import numpy as np
    from collections import Counter

    # 读取图像
    img = cv2.imread('../test4.jpg')

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 10, 150, apertureSize=3)

    #ret, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    #lines = cv2.HoughLinesP(binary, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)

    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=20)
    slopes = []
    #自己定义一个存储线段的元祖list
    line_info = []

    for line in lines:
        x1, y1, x2, y2 = line[0]
        #计算每条线针对自身的斜率

        slope = np.arctan2((y2 - y1), (x2 - x1)) * 180 / np.pi
        slope = round(slope)
        slopes.append(slope)
        line_info.append((x1, y1, x2, y2, slope))
        #cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    slope_counts = Counter(slopes)
    most_common_slopes = slope_counts.most_common(2)
    most_common_slope_1 = most_common_slopes[0][0]
    most_common_slope_2 = most_common_slopes[1][0]
    #筛选出所有斜率和最多的两个斜率之间差异小于10的线段
    selected_lines = []
    for line in line_info:
        x1, y1, x2, y2, slope = line
        if abs(slope - most_common_slope_1) < 5 or abs(slope - most_common_slope_2) < 5:
            selected_lines.append((x1, y1, x2, y2))
           # cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

    #设置边距
    dis_to_edge = 50
    left=dis_to_edge
    right=img.shape[1]-dis_to_edge
    top=dis_to_edge
    bottom=img.shape[0]-dis_to_edge
    print(left,right,top,bottom)
    #筛选出所有在边距外的线段
    for line in selected_lines:
        x1, y1, x2, y2 = line
        if x1 <= left and x2 <= left:
            cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
        elif x1 >= right and x2 >= right:
            cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
        elif y1 <= top and y2 <= top:
            cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
        elif y1 >= bottom and y2 >= bottom:
            cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)


    cv2.imshow('Result', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def grid_graph_old(image_original):
    #复制一个图片

    ###
    _row=10
    _col=10
    ###

    image=image_original.copy()
    custom_config = r'--oem 3 --psm 12'

    lines=[]
    d = pytesseract.image_to_data(image, config=custom_config,output_type=Output.DICT, lang='chi_sim')
    n_boxes = len(d['text'])
    for i in range(n_boxes):
        if int(d['conf'][i]) > 60:
            if d['text'][i]=='|':
                (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                lines.append((x, y, w, h))
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    #找到lines里的x和y的最大值和最小值

    x_min=min([x for x,y,w,h in lines])
    y_min=min([y for x,y,w,h in lines])
    x_max=max([x+w for x,y,w,h in lines])
    y_max=max([y+h for x,y,w,h in lines])
    #找到平均w和h
    w_avg=sum([w for x,y,w,h in lines])/len(lines)
    h_avg=sum([h for x,y,w,h in lines])/len(lines)

    #画一个网格
    #左上角的坐标
    x1=x_min
    y1=y_min
    #右上角的坐标
    x2=x_max
    y2=y_min
    #左下角的坐标
    x3=x_min
    y3=y_max
    #右下角的坐标
    x4=x_max
    y4=y_max
    #画线
    x1,y1,x2,y2,x3,y3,x4,y4=[int(x) for x in [x1,y1,x2,y2,x3,y3,x4,y4]]
    cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.line(image, (x1, y1), (x3, y3), (0, 0, 255), 2)
    cv2.line(image, (x2, y2), (x4, y4), (0, 0, 255), 2)
    cv2.line(image, (x3, y3), (x4, y4), (0, 0, 255), 2)

    #要在这个区域内进行切割,首先切成10行
    #每行的高度
    h_line=int((y4-y1)/_row)
    #每行的宽度
    w_line=int((x2-x1)/_col)
    for i in range(1,10):
        cv2.line(image, (x1, y1+i*h_line), (x2, y1+i*h_line), (0, 0, 255), 2)
        cv2.line(image, (x1+i*w_line, y1), (x1+i*w_line, y4), (0, 0, 255), 2)

    #划线后的图单独存储一次


    #最终将images的位置切成10*10的小图，并存储在对象返回，并记录每个图的位置序号
    image_res=image_original.copy()
    images_res={}
    for i in range(_col):
        for j in range(_row):
            x=x1+i*w_line
            y=y1+j*h_line
            w=w_line
            h=h_line
            roi = image_res[y:y + h, x:x + w]
            images_res[(i,j)]=roi #i 是列，j是行
    return images_res,image

def compare_images(imageA, imageB):

    imageA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    imageB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    imageA = cv2.resize(imageA, (100, 100))
    imageB = cv2.resize(imageB, (100, 100))
    #同时显示两个图
    score = ssim(imageA, imageB)
    #image_show(imageA, imageB)
    #print('之前分',score)
    score = (score+1)*50
    #print('之后分',score)

    return score


def grid_graph(image_original):

    #获得图片的宽高
    h,w,_=image_original.shape
    image=image_original.copy()

    #
    # ####这些是PDF的参数
    # ####参数区域
    # _row=10#要切分的行数
    # _col=10#要切分的列数
    #
    # w_left=0.111#识别区域距离图纸的左边的距离，占图纸最左边开始算的比例
    # w_right=0.887#识别区域距禽图纸的右边的距离，占图纸最左边开始算的比例
    # h_top=0.187#识别区域距离图纸的上边的距离，占图纸最上边开始算的比例
    # h_bottom=0.875#识别区域距离图纸的下边的距离，占图纸最上边开始算的比例
    #
    #
    # #内圈的间距
    #
    # w_inner_left=0.03
    # h_inner_top=0.02
    # w_inner_right=0.03
    # h_inner_bottom=0.02
    #
    # #每两行之间的间距
    # h_line_interval=0.011
    #



    ####这些是打印后的A4纸张的参数
    ####参数区域
    _row = 10  # 要切分的行数
    _col = 10  # 要切分的列数

    w_left = 0.145 # 识别区域距离图纸的左边的距离，占图纸最左边开始算的比例
    w_right = 0.86  # 识别区域距禽图纸的右边的距离，占图纸最左边开始算的比例
    h_top = 0.207  # 识别区域距离图纸的上边的距离，占图纸最上边开始算的比例
    h_bottom = 0.843  # 识别区域距离图纸的下边的距离，占图纸最上边开始算的比例

    # 内圈的间距

    w_inner_left = 0.03
    h_inner_top = 0.02
    w_inner_right = 0.03
    h_inner_bottom = 0.02

    # 每两行之间的间距
    h_line_interval = 0.011




    x1=w*w_left
    y1 = h*h_top
    # 右上角的坐标
    x2 =w*w_right
    y2 = h*h_top
    # 左下角的坐标
    x3 = w*w_left
    y3 = h*h_bottom
    # 右下角的坐标
    x4 = w*w_right
    y4 = h*h_bottom
    #测试的时候划线外圈
    x1, y1, x2, y2, x3, y3, x4, y4 = [int(x) for x in [x1, y1, x2, y2, x3, y3, x4, y4]]
    cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.line(image, (x1, y1), (x3, y3), (0, 0, 255), 2)
    cv2.line(image, (x2, y2), (x4, y4), (0, 0, 255), 2)
    cv2.line(image, (x3, y3), (x4, y4), (0, 0, 255), 2)


    h_line_interval=int(h*h_line_interval)
    x1=w*w_left+(w*(w_inner_left))
    y1 = h*h_top+(h*(h_inner_top))
    # 右上角的坐标
    x2 =w*w_right-(w*(w_inner_right))
    y2 = h*h_top+(h*(h_inner_top))
    # 左下角的坐标
    x3 = w*w_left+(w*(w_inner_left))
    y3 = h*h_bottom-(h*(h_inner_bottom))
    # 右下角的坐标
    x4 = w*w_right-(w*(w_inner_right))
    y4 = h*h_bottom-(h*(h_inner_bottom))
    # 画线
    x1, y1, x2, y2, x3, y3, x4, y4 = [int(x) for x in [x1, y1, x2, y2, x3, y3, x4, y4]]




    #要在这个区域内进行切割,首先切成10行
    #每行的高度
    h_line=int(((y4-y1)-h_line_interval*(_row-1))/_row)
    #每行的宽度
    w_line=int((x2-x1)/_col)
    for i in range(1,11):
        cv2.line(image, (x1, y1+(i-1)*h_line+(i-1)*h_line_interval), (x2, y1+(i-1)*h_line+(i-1)*h_line_interval), (0, 0, 255), 2)
        cv2.line(image, (x1, y1+(i)*h_line+(i-1)*h_line_interval), (x2, y1+(i)*h_line+(i-1)*h_line_interval), (0, 0, 255), 2)

        cv2.line(image, (x1+i*w_line, y1), (x1+i*w_line, y4), (0, 0, 255), 2)

        # 最终将images的位置切成10*10的小图，并存储在对象返回，并记录每个图的位置序号
    image_res = image_original.copy()
    images_res = {}
    for i in range(_col):
        for j in range(_row):
            x = x1 + i * w_line
            y = y1 + j * h_line+(j)*h_line_interval
            w = w_line
            h = h_line
            roi = image_res[y:y + h, x:x + w]
            images_res[(i, j)] = roi  # i 是列，j是行
    return images_res, image
def main(image_original):
    images_res,image_process = grid_graph(image_original)
    #印刷体和手写体对对应行数

    #显示一下images
    cv2.imshow('Result', image_process)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print_hand_related=((0,1),(2,3),(4,5),(6,7),(8,9))
    _col=10
    score_dict={}
    for a,b in print_hand_related:
        for i in range(_col):
            score=compare_images(images_res[(i,a)],images_res[(i,b)])
            score_dict[(i,a,b)]=score

    score = sum(score_dict.values()) / len(score_dict)
    print(score)
    return score_dict
def image_show(imageA, imageB):
    #将两个图片横向拼在一起显示
    imageA = cv2.resize(imageA, (100, 100))
    imageB = cv2.resize(imageB, (100, 100))
    image = np.hstack([imageA, imageB])
    cv2.imshow('Result', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()




if __name__ == '__main__':
    pic_name='biaozhun4.jpg'
    pic_name = 'bianzhuhao.jpg'
    image = cv2.imread(pic_name)
    res=main(image)
    print(res)
