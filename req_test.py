import requests
import os
import json
import hmac
import datetime
SECRET_KEY= '1001hbzh'
channel_id='1001'
# SECRET_KEY = SECRET_KEY + str(channel_id) + "_"
print('SECRET_KEY:', SECRET_KEY)
def generate_token(request_id, symbol_id, channel_id, timestamp):    # 获取当前时间，并精确到分钟
    message = 'channel_id=' + str(channel_id) + '&timestamp=' + str(timestamp)
    token = hmac.new(SECRET_KEY.encode(), message.encode(), 'sha256').hexdigest()
    print(message)
    return token


def upload_image():
    Request_Id='test'
    Channel_Id='1001'
    Symbol_Id='100000'
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    t = generate_token(Request_Id, Symbol_Id, Channel_Id, timestamp)
    print(t)
    res = requests.post('http://127.0.0.1:5000/uploadimage', files={'file': open('biaozhun.jpg', 'rb')},data={'Request_Id': Request_Id,'Channel_Id':Channel_Id,'Symbol_Id':Symbol_Id,'timestamp':timestamp},headers={'token': t})

    print(res.json())
    #print(res)
def get_history():
    t, ts = generate_token()
    res = requests.post('http://127.0.0.1:5000/history_order',headers={'Request-Id':t,'token':t,'Channel-Id':'1000','Symbol-Id':'test'})
    print(res.json())
if __name__ == '__main__':
    upload_image()
    #get_history()
