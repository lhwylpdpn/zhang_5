import os
import uuid
import time
import datetime
import hashlib
from .import graph_process as gp
import tempfile
import cv2
def logic_v1(file,request_id):
    uuid_ = str(uuid.uuid4()) + '_' + str(int(time.time()))


    with open('log_image/'+request_id+'_before.jpg','wb') as f:
        f.write(file.read())
        f.close()
    image = cv2.imread('log_image/'+request_id+'_before.jpg')
    #todo request_id 里可能有非法字符不一定可以保存成文件名，升级方向应该是随机文件名，然后数据库存关系

    images_res,image_process = gp.grid_graph(image)

    with open('process_image/'+request_id+'_'+uuid_+'_after.jpg','wb') as f:
        #将处理后的图片存储
        f.write(cv2.imencode('.jpg', image_process)[1].tostring())
        f.close()
    score_dict = {}
    print_hand_related = ((0, 1), (2, 3), (4, 5), (6, 7), (8, 9))
    _col = 10
    score_dict = {}
    for a, b in print_hand_related:
        for i in range(_col):
            score = gp.compare_images(images_res[(i, a)], images_res[(i, b)])
            score_dict[(i, a, b)] = score
    score = sum(score_dict.values()) / len(score_dict)

    #将分数划分几个档次，随机给出鼓励性质的评语
    if score>90:
        score_content='非常好，继续保持'
    elif score>80:
        score_content='很好，继续努力'
    elif score>70:
        score_content='还不错，继续加油'
    else:
        score_content='继续努力'


    #计算file的md5值
    file_md5 = hashlib.md5(file.read()).hexdigest()
    return uuid_,request_id,score,score_content,file_md5
