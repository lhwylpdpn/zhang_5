import requests
import os
import json
import hmac
import datetime
SECRET_KEY= '333'
def generate_token():
    # 获取当前时间，并精确到分钟
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    # 使用密钥和时间戳生成token
    token = hmac.new(SECRET_KEY.encode(), timestamp.encode(), 'sha256').hexdigest()
    return token, timestamp



if __name__ == '__main__':
    t, ts = generate_token()
    print(t)
    res = requests.post('http://127.0.0.1:5000/uploadimage',files={'file': open('upload/Cartoons_00038_07.jpg', 'rb')},headers={'token':t})
    print(res.text)




