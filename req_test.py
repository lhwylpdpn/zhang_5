import requests
import os
import json
import hmac
import datetime
SECRET_KEY= 'tokenTest'
def generate_token():
    # 获取当前时间，并精确到分钟
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    # 使用密钥和时间戳生成token
    token = hmac.new(SECRET_KEY.encode(), timestamp.encode(), 'sha256').hexdigest()
    return token, timestamp


def upload_image():
    t, ts = generate_token()
    res = requests.post('http://127.0.0.1:5000/uploadimage', files={'file': open('upload/test4.jpg', 'rb')},
                        headers={'token': t, 'Request-Id': t})
    print(res.json())

def get_history():
    t, ts = generate_token()
    res = requests.post('http://127.0.0.1:5000/history_order',headers={'Request-Id':t,'token':t})
    print(res.json())
if __name__ == '__main__':
    upload_image()
    get_history()
