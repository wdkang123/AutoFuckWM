import json
import demjson
import re
import requests
from model.conn import DataDao
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
    # 只操作为0的 因为2为暂停 3为异常 这两个情况都略过
    sql = "update auto_check set status=0 where status=1;"
    dao.execute_sql(sql)
    dao.close()

# 获取和激活token
def active_token_method():
    url = "http://" + str(server_ip) + ":" + str(server_port) + "/getKK"
    response = requests.get(url)
    data = response.text
    if data != "":
        url = "http://" + str(server_ip) + ":" + str(server_port) + "/active_token/" + str(data)
        response = requests.get(url)
        print(response.text)

# 打卡函数
def fuck_check():
    dao.connect(dao_url, dao_username, dao_password)
    # 0-开启打卡 | 1-已经打卡 | 2-关闭打卡 | 3-打卡异常 (3时为不打卡)
    # 查询出所有状态为0的用户
    sql = "select id, username, password, status from auto_check where status=0;"
    rows = dao.execute_sql(sql)
    # print(rows)
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
            print(resp)
            sql = "update auto_check set status='1' where id='" + str(user_id) + "';"
            dao.execute_sql(sql)
            # print(str(username) + "打卡成功")
            
        else:
            # 打卡异常
            sql = "update auto_check set status='3' where id='" + str(user_id) + "';"
            dao.execute_sql(sql)
            # 将异常信息写入数据库
            # 这里需要记录一下 有很多次异常了 但是不知道为什么异常了
            print(resp)
            sql = "insert into error_record values(default," + "'" + str(username) + "', '" + str(resp) + "', '" + str(time.strftime("%Y-%m-%d")) + "')"
            dao.execute_sql(sql)
        time.sleep(5)
    dao.close()


# 发送打卡报告
# 这块还不太行 看看怎么可以好看一些
def send_status():
    '''
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
            # 成功的
            html_string = str(html_string) + str(username) + ' : 成功' + "<br>"
        elif status == "2":
            # 暂停的
            html_string = str(html_string) + str(username) + ' : 暂停' + "<br>"
        else:
            # 其他情况都算失败的
            html_string = str(html_string) + str(username) + ' : 失败' + "<br>"
    server_msg = "http://pushplus.hxtrip.com/send?token=" + str(pp_token) + "&title=打卡统计表&content=" + str(html_string) + "&template=html&topic=user"
    requests.get(url=server_msg)
    '''
    dao.connect(dao_url, dao_username, dao_password)
    
    # 打卡总人数
    sql = "select count(id) from auto_check"
    rows = dao.execute_sql(sql)
    all_nums = 0
    for row in rows:
        all_nums = row[0]
    
    # 等待打卡的人数
    sql = "select count(*) from auto_check where status = 0"
    rows = dao.execute_sql(sql)
    wait_nums = 0
    for row in rows:
        wait_nums = row[0]

    # 打卡成功的人数
    sql = "select count(*) from auto_check where status = 1"
    rows = dao.execute_sql(sql)
    success_nums = 0
    for row in rows:
        success_nums = row[0]
    
    # 暂停打卡的人数
    sql = "select count(*) from auto_check where status = 2"
    rows = dao.execute_sql(sql)
    stop_nums = 0
    for row in rows:
        stop_nums = row[0]

    # 打卡异常(失败的)的人
    sql = "select username, status from auto_check where status = 3"
    rows = dao.execute_sql(sql)
    error_list = []
    for row in rows:
        item = {}
        item['username'] = str(row[0])
        item['status'] = str(row[1])
        error_list.append(item)

    # 准备提交打卡数据
    html_string = "愿大家四季平安健康!" + "<br>"
    html_string = str(html_string) + "早上5:15打卡(排队打卡) 微信推送8:15" + "<br>"
    html_string = str(html_string) + '<a href="https://kangkang2017.oss-cn-beijing.aliyuncs.com/%E8%87%AA%E5%8A%A8%E6%89%93%E5%8D%A1%E6%95%99%E7%A8%8B.mp4"><button>一分钟学会如何(打卡)更新数据</button></a>' + "<br>"
    html_string = str(html_string) + "-----" + "<br>"
    html_string = str(html_string) + "打卡总人数: " + str(all_nums) + "人 <br>"
    html_string = str(html_string) + "-----" + "<br>"
    html_string = str(html_string) + "成功人数: " + str(success_nums) + "人 <br>"
    html_string = str(html_string) + "等待人数(在早上5点后更新过打卡数据): " + str(wait_nums) + "人 <br>"
    html_string = str(html_string) + "暂停人数: " + str(stop_nums) + "人 <br>"
    html_string = str(html_string) + "打卡失败的列表: " + "<br>"
    # 遍历error_list
    # 判断是否为空
    html_string = str(html_string) + "-----" + "<br>"
    if len(error_list) == 0:
        html_string = str(html_string) + "T^T!啊哦···没有打卡失败的小伙伴" + "<br>"
    else:
        for each in error_list:
            html_string = str(html_string) + str(each['username']) + ' : 失败' + "<br>"
    html_string = str(html_string) + "-----" + "<br>"
    html_string = str(html_string) + \
        '<a href="http://wdkangtv.top:8086/fuck_all"><button>点击查看所有打卡状况</button></a>'
    html_string = str(html_string) + \
	'<a href="http://wdkangtv.top:8086/index"><button>点击进入打卡主页</button></a>'
    server_msg = "http://pushplus.hxtrip.com/send?token=" + \
        str(pp_token) + "&title=打卡统计表&content=" + \
        str(html_string) + \
        "&template=html&topic=user"
    dao.close()
    requests.get(url=server_msg)
    

# BlockingScheduler
scheduler = BlockingScheduler()

# date: 特定的时间点触发
# interval: 固定时间间隔触发
# cron: 在特定时间周期性地触发

# 21点15分重置等待打卡
scheduler.add_job(reset_status, 'cron', day_of_week='0-6', hour=23, minute=15)
scheduler.add_job(active_token_method, 'cron', day_of_week='0-6', hour=9, minute=20)
scheduler.add_job(fuck_check, 'cron', day_of_week='0-6', hour=9, minute=21)
# scheduler.add_job(send_status, 'cron', day_of_week='0-6', hour=8, minute=5)
print("========== 启动成功 ===========")
scheduler.start()
