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



def log_to_DB(request_id,score,score_content,file_md5,start_time,end_time):

    record_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    sql = "insert into `ai-eval`.record_info (request_id,score,score_content,file_md5,start_time,end_time,record_time) values ('{}',{},'{}','{}','{}','{}','{}')".format(request_id,score,score_content,file_md5,start_time,end_time,record_time)
    with MySQLConnection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
