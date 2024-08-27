import time

import cv2
import numpy as np
import math
import pytesseract
from pytesseract import Output
from skimage.metrics import structural_similarity as ssim
import graph_transform as gt


# 加载图片

def test1():
    image = cv2.imread('biaozhun4.jpg', 0)

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
    cv2.imshow('lines', line_image)
    cv2.waitKey(0)
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

def grid_graph(img):
    # 读取图像
    col=10
    row=10
    # Todo 投射转换，img输出是投射完的

    # 转换为灰度图像
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    src_img0 = cv2.GaussianBlur(gray,(3,3),0)
    src_img1 = cv2.bitwise_not(src_img0)
    AdaptiveThreshold = cv2.adaptiveThreshold(src_img1, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -2)

    horizontal = AdaptiveThreshold.copy()
    vertical = AdaptiveThreshold.copy()
    scale = 20

    horizontalSize = int(horizontal.shape[1] / scale)
    horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontalSize, 1))
    horizontal = cv2.erode(horizontal, horizontalStructure)
    horizontal = cv2.dilate(horizontal, horizontalStructure)

    verticalsize = int(vertical.shape[1] / scale)
    verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
    vertical = cv2.erode(vertical, verticalStructure, (-1, -1))
    vertical = cv2.dilate(vertical, verticalStructure, (-1, -1))
    mask = horizontal + vertical
    # 找到轮廓
    # OpenCV 3.x及之前版本
    if int(cv2.__version__.split('.')[0]) == 3:
        _, contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    # OpenCV 4及之后版本
    else:
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    #contours, _ = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    #contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    #打印图片的尺寸
    # cv2.imshow('Result', mask)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    x,y,w,h = 0,0,0,0
    for cnt in contours:
        t_x, t_y, t_w, t_h = cv2.boundingRect(cnt)
        #过滤足够大的轮廓
        if t_w > img.shape[1]/2 and  t_w<img.shape[1]*4/5  and  t_h > img.shape[0]/2 and  t_h<img.shape[0]*4/5:
            x, y, w, h = t_x, t_y, t_w, t_h

            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            break
    #如果找不到合适的轮廓，那么就直接使用整张纸继续寻找下面的内容
    if x==0 and y==0 and w==0 and h==0:
        x,y,w,h=0,0,img.shape[1],img.shape[0]

    gird_list=[]
    for cnt in contours:
        t_x, t_y, t_w, t_h = cv2.boundingRect(cnt)
        #只要在 x,y,w,h的范围内的轮廓
        if t_x>x and t_y>y and t_x+t_w<x+w and t_y+t_h<y+h:
            #cv2.rectangle(img, (t_x, t_y), (t_x + t_w, t_y + t_h), (0, 255, 0), 2)
            gird_list.append((t_x, t_y, t_w, t_h))
    image_res = img.copy()
    print('第一步找到的',len(gird_list))
    remove_list=[]
    for x, y, w, h in gird_list:
        if abs(w-h)>=10:
            remove_list.append((x, y, w, h))
    gird_list=[x for x in gird_list if x not in remove_list]
    print('remove后',len(gird_list))
    #对每个轮廓的 先y后x进行排序
    gird_list=sorted(gird_list,key=lambda x:(x[1],x[0]))


    #先检查是否有近似重叠的
    #假设精度够，那么w和h是可以被平均的
    min_x = min([x for x, y, w, h in gird_list])
    min_y = min([y for x, y, w, h in gird_list])
    max_x = max([x + w for x, y, w, h in gird_list])
    max_y = max([y + h for x, y, w, h in gird_list])
    w_avg=sum([w for x, y, w, h in gird_list])/len(gird_list)
    h_avg=sum([h for x, y, w, h in gird_list])/len(gird_list)
    cut_info={}
    j=0 #行
    i=0 #列
    for _ in range(len(gird_list)):
        if _==0: #第一行第一列
            cut_info[(i,j)]=(gird_list[_][0],gird_list[_][1],gird_list[_][2],gird_list[_][3])
            i+=1
        else:
            if gird_list[_][1]-gird_list[_-1][1]<h_avg*2/3:#还在同一行
                cut_info[(i,j)]=(gird_list[_][0],gird_list[_][1],gird_list[_][2],gird_list[_][3])
                i+=1
            else:
                j+=1
                i=0
                cut_info[(i,j)]=(gird_list[_][0],gird_list[_][1],gird_list[_][2],gird_list[_][3])
                i+=1
    print(len(list(cut_info.keys()))) #todo 后续这个地方可以做检查

    image_res = img.copy()
    images_res = {}

    for key in cut_info.keys():
        x, y, w, h = cut_info[key]
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        roi = image_res[y:y + h, x:x + w]
        images_res[key] = roi
    return images_res, img



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
    line_info = {}

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
    # 记录空白格部分的特征
    # #存储空白格的图片，也就是存储一次imageB
    # save_path='none_feature.jpg'
    # cv2.imwrite(save_path,imageB)

    none_feature = cv2.imread('none_feature.jpg')
    imageA_ = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    imageB_ = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    none_feature=cv2.cvtColor(none_feature, cv2.COLOR_BGR2GRAY)
    _, imageA_ = cv2.threshold(imageA_, 127, 255, cv2.THRESH_BINARY)
    _, imageB_ = cv2.threshold(imageB_, 127, 255, cv2.THRESH_BINARY)
    imageA_ = cv2.resize(imageA_, (100, 100))
    imageB_ = cv2.resize(imageB_, (100, 100))
    none_feature = cv2.resize(none_feature, (100, 100))
    #image_show(none_feature, imageB_)
    score=ssim(none_feature, imageB_)
    #print('ssim',score)
    if score>0.8:
        print('空白格')
        return 0

    #同时显示两个图
    imageA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    imageB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    imageA = cv2.resize(imageA, (100, 100))
    imageB = cv2.resize(imageB, (100, 100))
    score = ssim(imageA, imageB)
   # image_show(imageA, imageB)
    #print('之前分',score)
    score = (score+1)*50
    #print('之后分',score)




    return score



def  compare_images_pearson(imageA, imageB):
    from scipy.stats import pearsonr

    none_feature = cv2.imread('none_feature.jpg')
    imageA_ = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    imageB_ = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    none_feature = cv2.cvtColor(none_feature, cv2.COLOR_BGR2GRAY)
    _, imageA_ = cv2.threshold(imageA_, 127, 255, cv2.THRESH_BINARY)
    _, imageB_ = cv2.threshold(imageB_, 127, 255, cv2.THRESH_BINARY)
    imageA_ = cv2.resize(imageA_, (100, 100))
    imageB_ = cv2.resize(imageB_, (100, 100))
    none_feature = cv2.resize(none_feature, (100, 100))
    score = ssim(none_feature, imageB_)
    # print('ssim',score)
    if score > 0.8:
        print('空白格')
        return 0


    img_array_A = np.array(imageA_)
    img_array_B = np.array(imageB_)
    img_array_A = img_array_A.flatten()
    img_array_B = img_array_B.flatten()

    # 计算皮尔森相关系数
    correlation, _ = pearsonr(img_array_A, img_array_B)
    score = (correlation + 1) * 50
    return score


def compare_images_Tversky(imageA, imageB,alpha=0.5,beta=0.5):
    none_feature = cv2.imread('none_feature.jpg')

    imageA_ = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    imageB_ = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    none_feature = cv2.cvtColor(none_feature, cv2.COLOR_BGR2GRAY)
    _, imageA_ = cv2.threshold(imageA_, 127, 255, cv2.THRESH_BINARY)
    _, imageB_ = cv2.threshold(imageB_, 127, 255, cv2.THRESH_BINARY)
    imageA_ = cv2.resize(imageA_, (100, 100))
    imageB_ = cv2.resize(imageB_, (100, 100))
    none_feature = cv2.resize(none_feature, (100, 100))
    score = ssim(none_feature, imageB_)
    # print('ssim',score)
    if score > 0.8:
        #print('空白格')
        return 0


    img_array_A = imageA_.flatten()
    img_array_B = imageB_.flatten()
    #image_show(imageA_,imageB_)
    intersection = np.sum((img_array_A > 0) & (img_array_A > 0))
    only_a = np.sum((img_array_A > 0) & (img_array_B == 0))
    only_b = np.sum((img_array_B > 0) & (img_array_A == 0))
    tversky_index=intersection/(intersection+alpha*only_a+beta*only_b)
    #print('tversky_index',tversky_index,intersection,only_a,only_b)
    score = tversky_index*100
    return score


def compare_images_cosine(imageA, imageB):
    none_feature = cv2.imread('none_feature.jpg')

    imageA_ = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    imageB_ = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    none_feature = cv2.cvtColor(none_feature, cv2.COLOR_BGR2GRAY)
    _, imageA_ = cv2.threshold(imageA_, 127, 255, cv2.THRESH_BINARY)
    _, imageB_ = cv2.threshold(imageB_, 127, 255, cv2.THRESH_BINARY)
    imageA_ = cv2.resize(imageA_, (100, 100))
    imageB_ = cv2.resize(imageB_, (100, 100))
    none_feature = cv2.resize(none_feature, (100, 100))
    score = ssim(none_feature, imageB_)
    # print('ssim',score)
    if score > 0.8:
        #print('空白格')
        return 0

    imageA_ = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    imageB_ = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    imageA_ = cv2.resize(imageA_, (100, 100))
    imageB_ = cv2.resize(imageB_, (100, 100))

    img_array_A = imageA_.flatten()
    img_array_B = imageB_.flatten()

    dot_product = np.dot(img_array_A, img_array_B)
    norm_a = np.linalg.norm(img_array_A)
    norm_b = np.linalg.norm(img_array_B)
    cosine_similarity = dot_product / (norm_a * norm_b)

    return (cosine_similarity+1)*50

def grid_graph_v2(image_original,x=0,y=0,weigh=0,high=0):
    w, h = image_original.shape[1], image_original.shape[0]
    image = image_original.copy()
    if x!=0 and y!=0 and weigh!=0 and high!=0:
        x1 = x
        y1 = y
        x2 = x + weigh
        y2 = y
        x3 = x
        y3 = y + high
        x4 = x + weigh
        y4 = y + high
    else:
        x1 = 0
        y1 = 0
        x2 = w
        y2 = 0
        x3 = 0
        y3 = h
        x4 = w
        y4 = h

    x1, y1, x2, y2, x3, y3, x4, y4 = [int(x) for x in [x1, y1, x2, y2, x3, y3, x4, y4]]
    cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.line(image, (x1, y1), (x3, y3), (0, 0, 255), 2)
    cv2.line(image, (x2, y2), (x4, y4), (0, 0, 255), 2)
    cv2.line(image, (x3, y3), (x4, y4), (0, 0, 255), 2)

    w_inner_left = 0.03
    h_inner_top = 0.02
    w_inner_right = 0.03
    h_inner_bottom = 0.02

    # 每两行之间的间距
    h_line_interval = 0.011


    h_line_interval=int(h*h_line_interval)
    x1=x1+(w*(w_inner_left))
    y1 = y1+(h*(h_inner_top))
    # 右上角的坐标
    x2 =x2-(w*(w_inner_right))
    y2 = y2+(h*(h_inner_top))
    # 左下角的坐标
    x3 = x3+(w*(w_inner_left))
    y3 = y3-(h*(h_inner_bottom))
    # 右下角的坐标
    x4 = x4-(w*(w_inner_right))
    y4 = y4-(h*(h_inner_bottom))
    # 画线
    x1, y1, x2, y2, x3, y3, x4, y4 = [int(x) for x in [x1, y1, x2, y2, x3, y3, x4, y4]]
    cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.line(image, (x1, y1), (x3, y3), (0, 0, 255), 2)
    cv2.line(image, (x2, y2), (x4, y4), (0, 0, 255), 2)
    cv2.line(image, (x3, y3), (x4, y4), (0, 0, 255), 2)
    _col=10
    _row=10
    w_line = int((x2 - x1) / _col)

    #
    # cv2.imshow('Result', image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

def grid_graph_old_shouxie(image_original):

    #获得图片的宽高
    w,h=image_original.shape[1],image_original.shape[0]
    image=image_original.copy()
    #
    #
    # ##这些是PDF的参数
    # ##参数区域
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
    #
    #


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

    #

    x1, y1, x2, y2, x3, y3, x4, y4 = [int(x) for x in [x1, y1, x2, y2, x3, y3, x4, y4]]
    cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.line(image, (x1, y1), (x3, y3), (0, 0, 255), 2)
    cv2.line(image, (x2, y2), (x4, y4), (0, 0, 255), 2)
    cv2.line(image, (x3, y3), (x4, y4), (0, 0, 255), 2)


    # cv2.imshow('Result', image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # h_line_interval=int(h*h_line_interval)
    # x1=w*w_left+(w*(w_inner_left))
    # y1 = h*h_top+(h*(h_inner_top))
    # # 右上角的坐标
    # x2 =w*w_right-(w*(w_inner_right))
    # y2 = h*h_top+(h*(h_inner_top))
    # # 左下角的坐标
    # x3 = w*w_left+(w*(w_inner_left))
    # y3 = h*h_bottom-(h*(h_inner_bottom))
    # # 右下角的坐标
    # x4 = w*w_right-(w*(w_inner_right))
    # y4 = h*h_bottom-(h*(h_inner_bottom))
    # 画线


    #根据识别后的inner处理
    x1=x1+(w*(w_inner_left))
    y1 = y1+(h*(h_inner_top))
    # 右上角的坐标
    x2 =x2-(w*(w_inner_right))
    y2 = y2+(h*(h_inner_top))
    # 左下角的坐标
    x3 = x3+(w*(w_inner_left))
    y3 = y3-(h*(h_inner_bottom))
    # 右下角的坐标
    x4 = x4-(w*(w_inner_right))
    y4 = y4-(h*(h_inner_bottom))
    # 画线




    x1, y1, x2, y2, x3, y3, x4, y4 = [int(x) for x in [x1, y1, x2, y2, x3, y3, x4, y4]]

    print('a',x1,y1,x2,y2,x3,y3,x4,y4)


    #要在这个区域内进行切割,首先切成10行
    #每行的高度
    h_line=int(((y4-y1)-h_line_interval*(_row-1))/_row)
    #每行的宽度
    w_line=int((x2-x1)/_col)
    print('h_line',h_line)
    print('w_line',w_line)
    for i in range(1,11):
        #print('i',i,x1, int(y1+(i-1)*h_line+(i-1)*h_line_interval), x2, int(y1+(i-1)*h_line+(i-1)*h_line_interval))
        cv2.line(image, (x1, int(y1+(i-1)*h_line+(i-1)*h_line_interval)), (x2, int(y1+(i-1)*h_line+(i-1)*h_line_interval)), (0, 0, 255), 2)
        cv2.line(image, (x1, int(y1+(i)*h_line+(i-1)*h_line_interval)), (x2, int(y1+(i)*h_line+(i-1)*h_line_interval)), (0, 0, 255), 2)

        cv2.line(image, (int(x1+i*w_line), y1), (int(x1+i*w_line), y4), (0, 0, 255), 2)

        # 最终将images的位置切成10*10的小图，并存储在对象返回，并记录每个图的位置序号
    image_res = image_original.copy()
    images_res = {}
    for i in range(_col):
        for j in range(_row):
            x = x1 + i * w_line
            y = int(y1 + j * h_line+(j)*h_line_interval)
            w_tmp = w_line
            h_tmp = h_line
            print('w',x,y,int(y + h_tmp),int(x + w_tmp))
            roi = image_res[y:int(y + h_tmp), x:int(x + w_tmp)]
            images_res[(i, j)] = roi  # i 是列，j是行
    return images_res, image


import cv2
import numpy as np

def skeletonize(image):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, img_bin = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    skeleton = np.zeros(img_bin.shape, np.uint8)
    size = np.size(img_bin)
    skeleton_temp = np.zeros(img_bin.shape, np.uint8)
    kernel = np.ones((3, 3), np.uint8)

    while True:
        dilated = cv2.dilate(img_bin, kernel)
        temp = cv2.erode(img_bin, kernel)
        temp = cv2.subtract(dilated, temp)
        skeleton = cv2.bitwise_or(skeleton, temp)
        img_bin = cv2.erode(img_bin, kernel)

        if cv2.countNonZero(img_bin) == 0:
            break

    return skeleton




def main(image_original):
    images_res,image_process = grid_graph(gt.pers_transform(image_original))
    #印刷体和手写体对对应行数
    #显示一下images
    cv2.imshow('Result', image_process)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


    print_hand_related=((0,1),(2,3),(4,5),(6,7),(8,9))


    _col=10
    score_dict={}
    score_dict_2={}
    score_dict_3={}
    score_dict_4={}
    #print_hand_related=((1,3),(5,7))

    for a,b in print_hand_related:
        for i in range(_col):
            #align_images(images_res[(i,a)], images_res[(i,b)])
            try:
                score=compare_images(images_res[(i,a)],images_res[(i,b)])
                score_2=compare_images_pearson(images_res[(i,a)],images_res[(i,b)])
                score_3=compare_images_Tversky(images_res[(i,a)],images_res[(i,b)])
                score_4=compare_images_cosine(images_res[(i,a)],images_res[(i,b)])
            #

                # score=compare_images(skeletonize(images_res[(i,a)]),skeletonize(images_res[(i,b)]))
                # score_2=compare_images_pearson(skeletonize(images_res[(i,a)]),skeletonize(images_res[(i,b)]))
                # score_3=compare_images_Tversky(skeletonize(images_res[(i,a)]),skeletonize(images_res[(i,b)]))
                # score_4=compare_images_cosine(skeletonize(images_res[(i,a)]),skeletonize(images_res[(i,b)]))
            #捕获keyerror
            except KeyError:
                print('keyerror',i,a,b)
                continue

            score_dict[(i,a,b)]=score
            score_dict_2[(i,a,b)]=score_2
            score_dict_3[(i,a,b)]=score_3
            score_dict_4[(i,a,b)]=score_4

    #print(score_dict)
    score = sum(score_dict.values()) / len(score_dict)
    #print(score)
    score_2=sum(score_dict_2.values())/len(score_dict_2)
    #print(score_2)
    score_3=sum(score_dict_3.values())/len(score_dict_3)
    #print(score_3)
    score_4=sum(score_dict_4.values())/len(score_dict_4)
    return score,score_2,score_3,score_4
def image_show(imageA, imageB):
    #将两个图片横向拼在一起显示
    imageA = cv2.resize(imageA, (100, 100))
    imageB = cv2.resize(imageB, (100, 100))
    image = np.hstack([imageA, imageB])
    cv2.imshow('Result', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()



def align_images(img1, img2):
    import cv2
    import numpy as np

    # 读取图像
    # 二值化处理



    # 特征匹配
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    print(kp2,des2)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    print(bf,des1,des2)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)

    # 计算相似度评分
    similarity_score = len(matches) / max(len(kp1), len(kp2))
    print("Similarity Score:", similarity_score)


if __name__ == '__main__':


    pic_dict={'女儿':'bianzhuhao.jpg','儿子':'biaozhun4.jpg'}
    pic_dict['test1']='test1.jpg'
    pic_dict['test2']='test2.jpg'
    pic_dict['test3']='test3.jpg'
    pic_dict['test4']='test4.jpg'
    pic_dict['test5']='test5.jpg'
    for key in pic_dict.keys():
        pic_name=pic_dict[key]
        image = cv2.imread(pic_name)
        res=main(image)
        print(key,'方法1:ssim得分',res[0],'方法2:pearson得分',res[1],'方法3:Tversky得分',res[2],'方法4:cosine得分',res[3])


