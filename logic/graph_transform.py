import time

import cv2
import numpy as np


def cvShowResize(name, image, height=None):
    pass


def findContours(image, mode, method):
    # 轮廓检测
    # OpenCV 3.x及之前版本
    if int(cv2.__version__.split('.')[0]) == 3:
        _, contours, hierarchy = cv2.findContours(image, mode, method)
    # OpenCV 4及之后版本
    else:
        contours, hierarchy = cv2.findContours(image, mode, method)
    return contours, hierarchy


def orderPoints(pts):
    # 一共4个坐标点
    rect = np.zeros((4, 2), dtype="float32")

    # 按顺序找到对应坐标0123分别是 左上，右上，右下，左下
    # 计算左上，右下
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # 计算右上和左下
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def fourPointTransform(image, pts):
    # 获取输入坐标点
    rect = orderPoints(pts)
    (tl, tr, br, bl) = rect

    # 计算输入的w和h值
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # 变换后对应坐标位置
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    # 计算变换矩阵
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    # 返回变换后结果
    return warped


def resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]
    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))
    resized = cv2.resize(image, dim, interpolation=inter)
    return resized


def persTransform(image):
    orig = image.copy()
    # begin  -- use resize
    # 坐标也会相同变化
    ratio = image.shape[0] / 1000.0
    image = resize(orig, height=1000)
    # end

    # 预处理
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 75, 200)
    # 轮廓检测
    contours, hierarchy = findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    # 遍历轮廓
    screenCnt = None
    # 标准图像
    for c in contours:
        # 计算轮廓近似
        peri = cv2.arcLength(c, True)
        # C表示输入的点集
        # epsilon表示从原始轮廓到近似轮廓的最大距离，它是一个准确度参数
        # True表示封闭的
        approx = cv2.approxPolyDP(c, 0.01 * peri, True)

        # 4个点的时候就拿出来，判断宽、高>1/2 <  4/5
        if len(approx) == 4:
            t_x, t_y, t_w, t_h = cv2.boundingRect(c)
            if t_w > image.shape[1] / 2 and t_w < image.shape[1] * 4 / 5 and t_h > image.shape[0] / 2 and t_h < \
                    image.shape[0] * 4 / 5:
                screenCnt = approx
                break
    # 非标准图像，找到一个最大即可
    if screenCnt is None:
        for c in contours:
            # 计算轮廓近似
            peri = cv2.arcLength(c, True)
            # C表示输入的点集
            # epsilon表示从原始轮廓到近似轮廓的最大距离，它是一个准确度参数
            # True表示封闭的
            approx = cv2.approxPolyDP(c, 0.01 * peri, True)

            # 4个点的时候就拿出来
            if len(approx) == 4:
                screenCnt = approx
                break

    # 透视变换
    # begin -- use resize
    warped = fourPointTransform(orig, screenCnt.reshape(4, 2) * ratio)
    # end
    # begin -- no use resize
    # warped = fourPointTransform(orig, screenCnt.reshape(4, 2))
    # end
    return warped


def getContours(image):
    grey_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    grey_img = cv2.GaussianBlur(grey_img, (3, 3), 0)
    bitwise_not_img = cv2.bitwise_not(grey_img)
    AdaptiveThreshold = cv2.adaptiveThreshold(bitwise_not_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                                              15, -2)

    horizontal = AdaptiveThreshold.copy()
    vertical = AdaptiveThreshold.copy()
    scale = 20

    horizontalSize = int(horizontal.shape[1] / scale)
    horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontalSize, 1))
    horizontal = cv2.erode(horizontal, horizontalStructure)
    horizontal = cv2.dilate(horizontal, horizontalStructure)
    cvShowResize("horizontal", horizontal, 650)

    verticalsize = int(vertical.shape[1] / scale)
    verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
    vertical = cv2.erode(vertical, verticalStructure, (-1, -1))
    vertical = cv2.dilate(vertical, verticalStructure, (-1, -1))
    cvShowResize("vertical", vertical, 650)

    mask = horizontal + vertical
    # np.count_nonzero(mask, axis=0) #对列统计白色（非零值）
    # np.count_nonzero(mask, axis=1) #对行统计白色（非零值）
    cvShowResize("mask", mask, 650)

    net_img = cv2.bitwise_and(horizontal, vertical)
    cvShowResize("net_img", net_img, 650)

    # 轮廓检测
    contours, hierarchy = findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # =========================绘出所有轮廓=========================
    cnt_img = cv2.drawContours(image.copy(), contours, -1, (0, 0, 255), 2)
    cvShowResize('cnt_img', cnt_img, 650)
    # =============================================================
    return contours, hierarchy


def findTopContour(image, contours, hierarchy, cntIdx):
    area = cv2.contourArea(contours[cntIdx])
    if area > image.shape[0] * image.shape[1] * 1 / 2:
        childIndex = hierarchy[0][cntIdx][2]
        if childIndex != -1:
            area = cv2.contourArea(contours[childIndex])
            if area > image.shape[0] * image.shape[1] * 1 / 2:
                return findTopContour(image, contours, hierarchy, childIndex)
            else:
                return cntIdx
        else:
            return cntIdx
    else:
        nextIdx = hierarchy[0][cntIdx][0]
        if nextIdx != -1:
            return findTopContour(image, contours, hierarchy, nextIdx)
        else:
            return None


def getGridhNo1(image, contours, hierarchy, patch=True):
    col, row = 10, 10
    x, y, w, h = 0, 0, image.shape[1], image.shape[0]
    grid_list = []
    if len(contours) == 0:
        return grid_list

    # 查找最外层内容框
    cntIdx = None
    sortedCnts = sorted(contours, key=cv2.contourArea, reverse=True)
    area = cv2.contourArea(sortedCnts[0])
    if area > image.shape[0] * image.shape[1] * 1 / 2:
        cntIdx = findTopContour(image, contours, hierarchy, 0)
    if cntIdx is None:
        cntIdx = 0
    while cntIdx < len(contours):
        area = cv2.contourArea(contours[cntIdx])
        # 去掉杂乱的线
        if area < 200:
            cntIdx = cntIdx + 1
            continue
        t_x, t_y, t_w, t_h = cv2.boundingRect(contours[cntIdx])
        # 只要在 x,y,w,h的范围内的轮廓
        if t_x > x and t_y > y and t_x + t_w < x + w and t_y + t_h < y + h and abs(t_w - t_h) < 10:
            grid_list.append((t_x, t_y, t_w, t_h))

        cntIdx = cntIdx + 1

    print('第一步找到的', len(grid_list))

    # 对每个轮廓的 先y后x进行排序
    grid_list = sorted(grid_list, key=lambda x: (x[1], x[0]))

    # 求最大最小坐标
    min_x = min([x for x, y, w, h in grid_list])
    min_y = min([y for x, y, w, h in grid_list])
    max_x = max([x for x, y, w, h in grid_list])
    max_y = max([y for x, y, w, h in grid_list])
    w_avg = sum([w for x, y, w, h in grid_list]) / len(grid_list)
    h_avg = sum([h for x, y, w, h in grid_list]) / len(grid_list)

    # 创建初始值为None的二维数组
    table = [[None for _ in range(10)] for _ in range(10)]

    # 遍历grid_list
    rowIdx = 0
    for idx in range(len(grid_list)):
        x, y, w, h = grid_list[idx]
        colIdx = int((x - min_x + 10) / w_avg)
        if idx > 0 and y - grid_list[idx - 1][1] > h_avg * 2 / 3:
            rowIdx += 1
        table[rowIdx][colIdx] = (x, y, w, h)

    if patch:  # 是否补缺 i:行，j：列
        for i in range(len(table)):
            for j in range(len(table[i])):
                if table[i][j] is None:
                    notNoneRow = [t for t in table[i] if t is not None]
                    if len(notNoneRow) == 0:
                        print('注意!!! 此行一个格子也没识别，row：', i)
                        break
                    flagColIdx = j - 1  # 取前一个
                    if j == 0:  # 取第一个非None
                        flagColIdx = table[i].index(notNoneRow[0])

                    w_avg_row = sum([w for x, y, w, h in notNoneRow]) / len(notNoneRow)
                    h_avg_row = sum([h for x, y, w, h in notNoneRow]) / len(notNoneRow)
                    y_avg_row = sum([y for x, y, w, h in notNoneRow]) / len(notNoneRow)

                    x_patch = table[i][flagColIdx][0] + int(w_avg_row * (j - flagColIdx))
                    y_patch = int(y_avg_row)
                    if j > 0:  # 取左侧列的 y
                        y_patch = table[i][j - 1][1]
                    w_patch = int(w_avg_row)
                    h_patch = int(h_avg_row)
                    if i > 0:  # 取上一行同列的 w h
                        w_patch = table[i - 1][j][2]
                        h_patch = table[i - 1][j][3]

                    table[i][j] = (x_patch, y_patch, w_patch, h_patch)

    image_res = image.copy()
    images_res = {}

    for i in range(len(table)):
        for j in range(len(table[i])):
            if table[i][j] is None:
                continue
            x, y, w, h = table[i][j]
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            roi = image_res[y:y + h, x:x + w]
            images_res[(i, j)] = roi

    # 打印图片
    cvShowResize('grid', image, 650)
    print('最终找到的 ', len(images_res))
    return images_res, image


if __name__ == '__main__':
    # img_path = 'D:\\project\\AI\\evaluate\\testdata\\jt0821\\3.jpg'
    # img_path = 'D:\\project\\AI\\evaluate\\testdata\\wai13.jpg'
    img_path = 'biaozhun4.jpg'
    # img_path = 'D:\\project\\AI\\evaluate\\testdata\\oneblank.jpg'
    imgLoad = cv2.imread(img_path)
    pers_img = persTransform(imgLoad)

    pers_img_copyed = pers_img.copy()
    contours, hierarchy = getContours(pers_img)
    _, patchImg = getGridhNo1(pers_img, contours, hierarchy)
    #print('patchImg:', patchImg)
    print(len(_.keys()))


