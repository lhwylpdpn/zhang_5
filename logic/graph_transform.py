import time

import cv2
import numpy as np

def order_points(pts):
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


def four_point_transform(image, pts):
    # 获取输入坐标点
    rect = order_points(pts)
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

def is_four_point(cnt):
    # 计算轮廓近似
    peri = cv2.arcLength(cnt, True)
    # C表示输入的点集
    # epsilon表示从原始轮廓到近似轮廓的最大距离，它是一个准确度参数
    # True表示封闭的
    approx = cv2.approxPolyDP(cnt, 0.01 * peri, True)

    # 4个点的时候就拿出来
    if len(approx) == 4:
        return True
    return False

def pers_transform(image):
    orig = image.copy()
    # begin  -- use resize
    # 坐标也会相同变化
    ratio = image.shape[0] / 1000.0
    image = resize(orig, height = 1000)
    # end

    # 预处理
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 75, 200)
    # 轮廓检测
    # OpenCV 3.x及之前版本
    if int(cv2.__version__.split('.')[0]) == 3:
        cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[1]
    # OpenCV 4及之后版本
    else:
        cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[0]
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    # 遍历轮廓
    screenCnt = None
    # 标准图像
    for c in cnts:
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
        for c in cnts:
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
    warped = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)
    #end
    #begin -- no use resize
    # warped = four_point_transform(orig, screenCnt.reshape(4, 2))
    #end
    return warped


if __name__ == '__main__':
    img_path = 'D:\\project\\AI\\evaluate\\testdata\\jt0821\\5.jpg'
    # img_path = 'D:\\project\\AI\\evaluate\\testdata\\wai13.jpg'
    # img_path = 'D:\\project\\AI\\evaluate\\testdata\\zt.jpg'
    img_path='bianzhuhao.jpg'
    img = cv2.imread(img_path)
    img_transed = pers_transform(img)
    cv2.imshow("Original", resize(img, height=650))
    cv2.imshow("Transed", resize(img_transed, height=650))
    cv2.waitKey(0)
    cv2.destroyAllWindows()

