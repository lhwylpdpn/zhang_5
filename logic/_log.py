import pymysql
import time
import configparser


class MySQLConnection(object):

    def __init__(self, select_db='rds'):
        if select_db == 'rds':
            cf = configparser.ConfigParser()
            filename = 'config//DB.conf'
            cf.read(filename, encoding='utf-8')
            self.__host = cf.get('DB', 'host')
            self.__port = int(cf.get('DB', 'port'))
            self.__user = cf.get('DB', 'user')
            self.__password = cf.get('DB', 'pwd')
            self.__charset = cf.get('DB', 'charset')

        self.conn = pymysql.connect(host=self.__host, port=self.__port,
                                    user=self.__user, password=self.__password,
                                    charset=self.__charset)
        self.cur = self.conn.cursor

    # self.conn_str= 'mysql+pymysql://{}:{}@{}:{}/{}?charset={}'.format(self.__user, self.__password, self.__host, self.__port, 'binance', self.__charset)
    # self.engine = create_engine(self.conn_str)
    @property
    def cursor(self):
        return self.cur

    def commit(self):
        return self.conn.commit()

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.commit()
            self.conn.close()



def log_to_DB(request_id,service_id,score,score_content,file_md5,start_time,end_time,symbol_id,channel_id):

    record_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    sql = "insert into `ai-eval`.record_info (request_id,score,score_content,file_md5,start_time,end_time,record_time,service_id,symbol_id,channel_id) values ('{}',{},'{}','{}','{}','{}','{}','{}','{}','{}')".format(request_id,score,score_content,file_md5,start_time,end_time,record_time,service_id,symbol_id,channel_id)
    with MySQLConnection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()

#将每张进行识别的图，和识别前的图都进行存储
def log_to_db_request(request_id,header_info):
    record_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    header_info=header_info.__repr__()
    #替换掉里面的单引号
    header_info=header_info.replace("'",'"')
    sql = "insert into `ai-eval`.client_requests (request_id,header_info,updated_at) values ('{}','{}','{}')".format(request_id,header_info,record_time)
    with MySQLConnection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()


def get_history_order_info(request_id,symbol_id,channel_id):
    """

    :param request_id:
    判断request_id 是否是字符串,是否有特殊字符，不是字符串要返回报错
    是字符串，查数据库，结果按照同步返回的一样
    如果是多条仅仅返回时间靠前的这条
    后续增加了其他参数，再扩展

    :param symbol_id:
    强制转换成字符串
    然后如果是空字符串,要去除where条件，返回所有symbol_id的记录

    :param channel_id:
    强制转换成字符串
    不负责空的问题，直接加入where条件

    :return:
    return一个完整的json
    """
    if type(request_id) != str:
        #如果不是字符串,强制转成字符串
        request_id=str(request_id)
    if type(symbol_id) != str:
        #如果不是字符串,强制转成字符串
        symbol_id=str(symbol_id)
    if type(channel_id) != str:
        #如果不是字符串,强制转成字符串
        channel_id=str(channel_id)

    sql="""select score,score_content,service_id,request_id,file_md5,start_time,end_time
    from `ai-eval`.record_info
    where request_id='"""+request_id+"""' 
    and channel_id='"""+channel_id+"""'
    
    """
    if symbol_id!='':
        sql+=" and symbol_id='"+symbol_id+"'"
    sql+=' order by start_time desc  limit 1;'
    with MySQLConnection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        res=cursor.fetchall()
        conn.commit()
        cursor.close()
    #将res转成json
    if len(res)==0:
        return {'message':'request_id not found','code':1106}
    res=res[0]
    res={'score':res[0],'score_content':res[1],'service_id':res[2],'request_id':res[3],'file_md5':res[4],'start_time':str(res[5]),'end_time':str(res[6])}
    res={'message': 'get history_order successfully', 'code': 200, 'body': res}
    return res

if __name__ == '__main__':
    #打印python的版本,不是pymysql
    import sys
    print(sys.version)