import json
import demjson
import re
import requests
from MySqlConn import DataDao
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime


server_ip = ""
server_port = ""

# pushplus
pp_token = ""

# database
dao = DataDao()
dao_url = ""
dao_username = ""
dao_password = ""

# 重置状态
def reset_status():
    dao.connect(dao_url, dao_username, dao_password)
    sql = "update auto_check set status=0 where status=1;"
    dao.execute_sql(sql)
    dao.close()

# 打卡函数
def fuck_check():
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
        # 0-开启打卡 | 1-已经打卡 | 2-关闭打卡 | 3-打卡异常 (3时为不打卡)
        # 在首页提交数据后 状态会调整为0
        if str(resp) == "打卡成功":
            sql = "update auto_check set status='1' where id='" + str(user_id) + "';"
            dao.execute_sql(sql)
            # print(str(username) + "打卡成功")
        else:
            sql = "update auto_check set status='3' where id='" + str(user_id) + "';"
            dao.execute_sql(sql)
        time.sleep(5)
    dao.close()


# 发送打卡报告
def send_status():
    sql = "select username, status from auto_check ORDER BY username;"
    dao.connect(dao_url, dao_username, dao_password)
    rows = dao.execute_sql(sql)
    dao.close()
    html_string = """<table cellpadding="0" cellspacing="0" style="line-height:25px;">
        <tr>
            <th style="border:1px solid #aaa">账号</th>
            <th style="border:1px solid #aaa">名字</th>
            <th style="border:1px solid #aaa">打卡状态</th>
        </tr>"""
    for row in rows:
        username = row[0]
        status = rows[1]
        if str(status) == "1":
            html_string = str(html_string) + f"""
            <tr>
                <td style="text-align:center;border:1px solid #aaa">{username}</td>
                <td style="text-align:center;border:1px solid #aaa">打卡成功</td>
            </tr>
            """
        else:
            html_string = str(html_string) + f"""
            <tr>
                <td style="text-align:center;border:1px solid #aaa">{username}</td>
                <td style="text-align:center;border:1px solid #aaa">打卡失败</td>
            </tr>
            """
    html_string = str(html_string) + "</table>"
    server_msg = "http://pushplus.hxtrip.com/send?token=" + str(pp_token) + "&title=打卡成功统计表&content=" + str(html_string) + "&template=html&topic=user"
    requests.get(url=server_msg)


# BlockingScheduler
scheduler = BlockingScheduler()

# date: 特定的时间点触发
# interval: 固定时间间隔触发
# cron: 在特定时间周期性地触发

# 21点15分重置等待打卡
scheduler.add_job(reset_status, 'cron', day_of_week='1-7', hour=21, minute=15)
scheduler.add_job(fuck_check, 'cron', day_of_week='1-7', hour=5, minute=30)
scheduler.add_job(send_status, 'cron', day_of_week='1-7', hour=8, minute=00)
scheduler.start()
