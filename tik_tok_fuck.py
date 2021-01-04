import json
import demjson
import re
import requests
from MySqlConn import DataDao
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

# config
import configparser


# config
cfg = configparser.ConfigParser()
cfg.read("config.ini")

# 你flask启动的服务
server_ip = str(cfg.get("server", "SERVER_IP"))
server_port = str(cfg.get("server", "SERVER_PORT"))

# pushplus的token
pp_token = str(cfg.get("server", "PUSHPLUAH_TOKEN"))

# database
dao = DataDao()
dao_url = str(cfg.get("mysql", "HOST"))
dao_username = str(cfg.get("mysql", "USERNAME"))
dao_password = str(cfg.get("mysql", "PASSWORD"))


# 重置状态
def reset_status():
    dao.connect(dao_url, dao_username, dao_password)
    sql = "update auto_check set status=0 where status=1;"
    dao.execute_sql(sql)
    dao.close()

# 打卡函数
def fuck_check():
    dao.connect(dao_url, dao_username, dao_password)
    # 0-开启打卡 | 1-已经打卡 | 2-关闭打卡 | 3-打卡异常 (3时为不打卡)
    # 查询出所有状态为0的用户
    sql = "select id, username, password, status from auto_check where status=0;"
    rows = dao.execute_sql(sql)
    for row in rows:
         # 正常打卡
        user_id = row[0]
        username = row[1]
        password = row[2]
        url = "http://" + str(server_ip) + ":" + str(server_port) + "/fuck_it/" + str(username) + "/" + str(password)
        response = requests.get(url)
        resp = response.text
        # 在首页提交数据后 状态会调整为0
        if str(resp) == "打卡成功":
            # 打卡成功
            sql = "update auto_check set status='1' where id='" + str(user_id) + "';"
            dao.execute_sql(sql)
            # print(str(username) + "打卡成功")
        else:
            # 打卡异常
            sql = "update auto_check set status='3' where id='" + str(user_id) + "';"
            dao.execute_sql(sql)
            # 将异常信息写入数据库
            # 这里需要记录一下 有很多次异常了 但是不知道为什么异常了
            sql = "insert into error_record values(default," + "'" + str(username) + "', '" + str(resp) + "', '" + str(time.strftime("%Y-%m-%d")) + "')"
            dao.execute_sql(sql)
        time.sleep(5)
    dao.close()


# 发送打卡报告
def send_status():
    dao.connect(dao_url, dao_username, dao_password)
    sql = "select username, status from auto_check ORDER BY username;"
    rows = dao.execute_sql(sql)
    dao.close()
    html_string = ''
    for row in rows:
        username = str(row[0])
        status = str(row[1])
        username = str(username[0:2]) + "*" + str(username[7:11])
        if status == "1":
            html_string = str(html_string) + str(username) + ' : 成功' + "<br>"
        else:
            html_string = str(html_string) + str(username) + ' : 失败' + "<br>"
    server_msg = "http://pushplus.hxtrip.com/send?token=" + str(pp_token) + "&title=打卡统计表&content=" + str(html_string) + "&template=html&topic=user"
    requests.get(url=server_msg)


# BlockingScheduler
scheduler = BlockingScheduler()

# date: 特定的时间点触发
# interval: 固定时间间隔触发
# cron: 在特定时间周期性地触发

# 21点15分重置等待打卡
scheduler.add_job(reset_status, 'cron', day_of_week='0-6', hour=21, minute=15)
scheduler.add_job(fuck_check, 'cron', day_of_week='0-6', hour=5, minute=30)
scheduler.add_job(send_status, 'cron', day_of_week='0-6', hour=8, minute=15)
print("========== 启动成功 ===========")
scheduler.start()
