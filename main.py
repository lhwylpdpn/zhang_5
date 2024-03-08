# 导入flask和其他必要的库
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import hmac
import datetime
# 创建一个flask应用对象
app = Flask(__name__)
SECRET_KEY = 'tokenTest'

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
def generate_token():
    # 获取当前时间戳
    timestamp = timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    # 使用密钥和时间戳生成token
    token = hmac.new(SECRET_KEY.encode(), timestamp.encode(), 'sha256').hexdigest()
    return token, timestamp

# 定义一个路由，用于处理图片上传的请求
@app.route('/uploadimage', methods=['POST'])
def upload_file():
    # 检查请求中是否有文件
    print(333)
    #打印request的内容
    if 'file' not in request.files:
        return jsonify({'message': 'No file part', 'code': 400})
    file = request.files['file']
    #token来自于header里面的token

    token = request.headers.get('token','') if request.headers.get('token','') else request.args.get('token','')
    print(token)


    #判断token的逻辑
    current_token, timestamp = generate_token()
    if token != current_token:
        return jsonify({'message': 'Invalid token', 'code': 1100})



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

    #打印文件名,并且返回成功
    print(file.filename)
    return jsonify({'message': 'File uploaded successfully', 'code': 200})




    # 运行flask应用
if __name__ == '__main__':
    app.run()
