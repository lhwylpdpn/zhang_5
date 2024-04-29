import os
import uuid
import time
import datetime
import hashlib
def test_logic(file,request_id):


    score = 84
    score_content = '整体书写比较好,有85%的字体书写非常棒，有12%的仍有提高空间'
    uuid_=str(uuid.uuid4())+'_'+str(int(time.time()))
    #计算file的md5值
    file_md5 = hashlib.md5(file.read()).hexdigest()
    return uuid_,request_id,score,score_content,file_md5
