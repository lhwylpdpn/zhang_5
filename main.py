# 导入flask和其他必要的库
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import hmac
import datetime
import logic.api_logic as api_
import time
import logic._log as log_
# 创建一个flask应用对象
app = Flask(__name__)
SECRET_KEY = 'tokenTest'

#20240722增加一个secret_channel，用于区分不同的channel
SECRET_channel =[]
SECRET_channel.append('1000')#都需要是字符串，整型会影响其他判断
SECRET_channel.append('1001')
SECRET_channel.append('1002')
SECRET_channel.append('1003')

# 设置一个保存图片的文件夹
UPLOAD_FOLDER = 'upload'
# 设置允许上传的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# 设置图片的最大大小为10MB
MAX_CONTENT_LENGTH = 10 * 1024 * 1024

# 检查文件名是否符合要求
def allowed_file(filename):
    return '.' in filename and  filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 生成token的函数

def generate_token(request_id, symbol_id, channel_id, timestamp):
    # 获取当前时间戳
    # 使用密钥和时间戳生成token
    token_dict={}
    #20240722 token的生成逻辑变更，增加channel的判断，然后返回一个dict，key是channle，value是token，用于后续的判断
    for  channel in SECRET_channel:
        SECRET_KEY_tmp = SECRET_KEY + str(channel) + "_"
        if channel=='1000':
            SECRET_KEY_tmp="1000xxl"
        if channel=='1001':
            SECRET_KEY_tmp="1001hbzh"
        message = 'channel_id='+str(channel_id)+'&timestamp='+str(timestamp)
        print('message:',message)
        token = hmac.new(SECRET_KEY_tmp.encode(), message.encode(), 'sha256').hexdigest()
        token_test='test'


        # token1 = hmac.new(SECRET_KEY_tmp.encode(),
        #                   (datetime.datetime.now() - datetime.timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M').encode(),
        #                   'sha256').hexdigest()
        # token2 = hmac.new(SECRET_KEY_tmp.encode(),
        #                   (datetime.datetime.now() - datetime.timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M').encode(),
        #                   'sha256').hexdigest()
        # token3 = hmac.new(SECRET_KEY_tmp.encode(),
        #                   (datetime.datetime.now() + datetime.timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M').encode(),
        #                   'sha256').hexdigest()
        # token4 = hmac.new(SECRET_KEY_tmp.encode(),
        #                   (datetime.datetime.now() + datetime.timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M').encode(),
        #                   'sha256').hexdigest()
        token_list = [token,token_test]
        token_dict[channel]=token_list



    #增加用于测试的token
    return token_dict

# 定义一个路由，用于处理图片上传的请求
@app.route('/uploadimage', methods=['POST'])
def upload_file():
    # 检查请求中是否有文件
    #打印request的内容
    if 'file' not in request.files:
        return jsonify({'message': 'No file part', 'code': 400})
    file = request.files['file']
    #token来自于header里面的token

    form_lower = {k.lower(): v for k, v in request.form.to_dict().items()}


    token = request.headers.get('token','')
    request_id = form_lower.get('request_id','')
    symbol_id = form_lower.get('symbol_id', '')
    channel_id= form_lower.get('channel_id','')
    timestamp = form_lower.get('timestamp','')
    if channel_id not in SECRET_channel:
        return jsonify({'message': 'Invalid channel', 'code': 1107})
    token_dict = generate_token(request_id=request_id, symbol_id=symbol_id, channel_id=channel_id, timestamp=timestamp)

    if token not in token_dict.get(channel_id,[]):
        print('token:',token,'token_list:',token_dict.get(channel_id,[]),'channel_id',channel_id)
        #print('token:',token,'token_list:',token_dict.get(channel_id,[]),'channel_id',channel_id)
        return jsonify({'message': 'Invalid token', 'code': 1100})



    #先存储一次request_id方便查询
    header_info=request.headers
    log_.log_to_db_request(request_id,header_info)


    #目标是接到一个文件，并能直接print出文件的内容，会进行如下的一些检查
    # 如果没有传文件名或者为空,则返回错误信息
    # 如果文件格式不符合要求,则返回错误信息
    # 如果文件大小太大,则返回错误信息
    # 如果文件无法识别,则返回错误信息
    # 为上述内容定义错误的状态码
    if file.filename == '':
        return jsonify({'message': 'No selected file', 'code': 1101})
    if not allowed_file(file.filename):
        return jsonify({'message': 'File format not supported', 'code': 1102})
    if file.content_length > MAX_CONTENT_LENGTH:
        return jsonify({'message': 'File size too large', 'code': 1103})

    try:
        start_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #print(len(file.read()))
        uuid_,request_id,score,score_content,file_md5 = api_.logic_v1(file,request_id)
        end_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_.log_to_DB(request_id,uuid_,score,score_content,file_md5,start_time,end_time,symbol_id,channel_id)
    except Exception as e:
        #打印具体哪儿行出错

        print(e)
        return jsonify({'message': 'File cannot be read', 'code': 1104})

    #打印文件名,并且返回成功
    return jsonify({'message': 'File uploaded successfully', 'code': 200,'body': {'score':score,'score_content':score_content,'service_id':uuid_,'request_id':request_id,'file_md5':file_md5,'timestamp':int(time.time())}})




    # 运行flask应用


@app.route('/history_order', methods=['POST'])
def get_order():
    token = request.headers.get('token', '')
    request_id = request.headers.get('request_id', '')

    #20240722 增加channel的判断
    symbol_id = request.headers.get('symbol_id', '')
    channel_id= request.headers.get('channel_id','')
    if channel_id not in SECRET_channel:
        return jsonify({'message': 'Invalid channel', 'code': 1107})
    token_dict, timestamp = generate_token()
    if token not in token_dict.get(channel_id,[]):
        #print('token:',token,'token_list:',token_dict.get(channel_id,[]),'channel_id',channel_id)
        return jsonify({'message': 'Invalid token', 'code': 1100})
    #如果没有request_id,则返回错误信息
    if request_id == '':
        return jsonify({'message': 'Invalid request_id', 'code': 1105})

    try:
        res = log_.get_history_order_info(request_id,symbol_id,channel_id)
    except Exception as e:
        print(e)
        return jsonify({'message': 'System error', 'code': 4001})
    return jsonify(res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
