import time

import cv2
import numpy as np
import math
import pytesseract
from pytesseract import Output
from skimage.metrics import structural_similarity as ssim
# 加载图片

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



def compare_images(imageA, imageB):
    # 记录空白格部分的特征
    # #存储空白格的图片，也就是存储一次imageB
    # save_path='none_feature.jpg'
    # cv2.imwrite(save_path,imageB)

    none_feature = cv2.imread('none_feature.jpg')
    #imageA_ = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    #imageB_ = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    none_feature=cv2.cvtColor(none_feature, cv2.COLOR_BGR2GRAY)
    _, imageA_ = cv2.threshold(imageA, 127, 255, cv2.THRESH_BINARY)
    _, imageB_ = cv2.threshold(imageB, 127, 255, cv2.THRESH_BINARY)
    imageA_ = cv2.resize(imageA_, (100, 100))
    imageB_ = cv2.resize(imageB_, (100, 100))
    none_feature = cv2.resize(none_feature, (100, 100))

    score=ssim(none_feature, imageB_)
    #print('ssim',score)
    if score>0.8:
        print('空白格')
        return 0

    #同时显示两个图
    #imageA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    #imageB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    imageA = cv2.resize(imageA, (100, 100))
    imageB = cv2.resize(imageB, (100, 100))
    score = ssim(imageA, imageB)
    #image_show(imageA, imageB)
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

def skeletonize(img):

    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    img = cv2.GaussianBlur(img, (5, 5), 0)
    skeleton = cv2.ximgproc.thinning(img)
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
                #score=compare_images(images_res[(i,a)],images_res[(i,b)])
                #score_2=compare_images_pearson(images_res[(i,a)],images_res[(i,b)])
                #score_3=compare_images_Tversky(images_res[(i,a)],images_res[(i,b)])
                #score_4=compare_images_cosine(images_res[(i,a)],images_res[(i,b)])

                score=compare_images(skeletonize(images_res[(i,a)]),skeletonize(images_res[(i,b)]))
                #score_2=compare_images_pearson(skeletonize(images_res[(i,a)]),skeletonize(images_res[(i,b)]))
                #score_3=compare_images_Tversky(skeletonize(images_res[(i,a)]),skeletonize(images_res[(i,b)]))
                #score_4=compare_images_cosine(skeletonize(images_res[(i,a)]),skeletonize(images_res[(i,b)]))
            #捕获keyerror
            except KeyError:
                print('keyerror',i,a,b)
                continue

            score_dict[(i,a,b)]=score
            # score_dict_2[(i,a,b)]=score_2
            # score_dict_3[(i,a,b)]=score_3
            # score_dict_4[(i,a,b)]=score_4

    #print(score_dict)
    score = sum(score_dict.values()) / len(score_dict)
    #print(score)
    score_2=sum(score_dict_2.values())/len(score_dict_2) if len(score_dict_2)>0 else 0
    #print(score_2)
    score_3=sum(score_dict_3.values())/len(score_dict_3) if len(score_dict_3)>0 else 0
    #print(score_3)
    score_4=sum(score_dict_4.values())/len(score_dict_4) if len(score_dict_4)>0 else 0
    return score,score_2,score_3,score_4
def image_show(imageA, imageB):
    #将两个图片横向拼在一起显示
    imageA = cv2.resize(imageA, (100, 100))
    imageB = cv2.resize(imageB, (100, 100))
    image = np.hstack([imageA, imageB])
    cv2.imshow('Result', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()



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


