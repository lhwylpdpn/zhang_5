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
        score_content="""
        *你的书写非常规范，体现出优秀的书写习惯。
        整体布局合理大方，书写工整美观，令人赏心悦目。
        大小匀称，占格合理，体现出十字八点格的特点。
        非常棒，继续保持！"""
    elif score>80:
        score_content="""
        *你的书写较为规范，能准确把握字的结构，还有提升空间。
        整体布局合理，显示出你良好的书写习惯。
        结构合理，在十字八点格中占位准确。
        注意细节，相信你可以做的更好！"""
    elif score>70:
        score_content="""
        *你的书写有一定的书写基础，在清晰度和规范性方面有待提高。
        整体还可以，要更注重书写的质量和细节哦。
        结构不够紧凑，需要十字八点定位练习汉字的结构。
        勤加练习，相信你可以做的更好！
        """
    elif score>60:
        score_content="""
        *你的书写在规范性和清晰度上都有很大的提升空间。
        书写中存在多处错误和不规范的字形，建议多花时间进行书写训练。
        笔画之间缺乏连贯性，建议从十字八点法的基础笔画开始练习。
        勤加练习，相信你也可以做的更好！
        """
    else:
        score_content="""
        *你的书写质量较差，需要从根本上改变书写习惯。
        书写很不规范，要重视书写问题，从基础开始认真练习。
        缺乏基本的书写规范，字形随意，建议系统学习十字八点法。
        坚持不懈得练习，一定会有提高，加油！
        """


    #计算file的md5值
    file_md5 = hashlib.md5(file.read()).hexdigest()
    return uuid_,request_id,score,score_content,file_md5
