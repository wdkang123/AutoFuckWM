import pymysql


class DataDao(object):
    def __init__(self):
        self.host = ""
        self.user = ""
        self.password = ""
        self.port = ""
        self.mysql_conn = {}
        self.mysql_cur = {}
        self.is_connect = False

    def connect(self, host, user, password, port):
        self.host = host
        self.user = user
        self.password = password
        self.mysql_conn = pymysql.connect(
            host = host,
            user = user,
            password = password,
            port = port,
            database = "auto_fuck",
            charset = "utf8"
        )
        self.mysql_cur = self.mysql_conn.cursor()

    def execute_sql(self, mysql_sql):
        self.mysql_cur.execute(mysql_sql)
        self.mysql_conn.commit()
        return self.mysql_cur.fetchall()

    def close(self):
        self.mysql_cur.close()
        self.mysql_conn.close()
