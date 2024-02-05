# 导入flask和其他必要的库
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os

# 创建一个flask应用对象
app = Flask(__name__)

# 设置一个保存图片的文件夹
UPLOAD_FOLDER = 'upload'
# 设置允许上传的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# 设置图片的最大大小为10MB
MAX_CONTENT_LENGTH = 10 * 1024 * 1024

# 检查文件名是否符合要求
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 定义一个路由，用于处理图片上传的请求
@app.route('/upload', methods=['POST'])
def upload_file():
    # 检查请求中是否有文件
    #打印request的内容
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'})
    file = request.files['file']
    # 检查文件是否为空
    if file.filename == '':
        return jsonify({'message': 'No selected file'})
    # 检查文件是否符合要求
    if file and allowed_file(file.filename):
        # 为文件名添加安全性
        filename = secure_filename(file.filename)
        # 保存文件到指定的文件夹
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        # 返回成功的信息
        return jsonify({'message': 'File received'})
    else:
        # 返回失败的信息
        return jsonify({'message': 'Invalid file type'})

# 运行flask应用
if __name__ == '__main__':
    app.run()
