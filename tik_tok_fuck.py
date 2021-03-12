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
pp_group = str(cfg.get("server", "PUSHPLUAH_GROUP"))

# database
dao = DataDao()
dao_url = str(cfg.get("mysql", "HOST"))
dao_username = str(cfg.get("mysql", "USERNAME"))
dao_password = str(cfg.get("mysql", "PASSWORD"))
dao_port = str(cfg.get("mysql", "PORT"))

# tiktok 打卡时间
reset_hour = str(cfg.get("tiktok", "RESET_HOUR"))
reset_minute = str(cfg.get("tiktok", "RESET_MINUTE"))
tik_hour = str(cfg.get("tiktok", "TIK_HOUR"))
tik_minute = str(cfg.get("tiktok", "TIK_MINUTE"))
push_hour = str(cfg.get("tiktok", "PUSH_HOUR"))
push_minute = str(cfg.get("tiktok", "PUSH_MINUTE"))

# 重置状态
def reset_status():
    dao.connect(dao_url, dao_username, dao_password, dao_port)
    # 只操作为0的 因为2为暂停 3为异常 这两个情况都略过
    sql = "update auto_check set status=0 where status=1;"
    dao.execute_sql(sql)
    dao.close()

# 一人toekn 多人打卡
def new_fuck():
    # 获取最新的token来打卡
    token = ""
    # 一人打卡多人token的那个用户的账号和密码
    username = ""
    password = ""
    url = "http://" + str(server_ip) + ":" + str(server_port) + "/get_token/" + str(username) + "/" + str(password)
    response = requests.get(url)
    resp = response.text
    error_list = re.findall(str("error"), str(resp), re.S | re.M)
    if error_list:
        print("获取失败token")
        return "获取token失败"
    token = str(resp)
    print(token)
    # 获取所有需要打卡的用户
    dao.connect(dao_url, dao_username, dao_password, dao_port)
    sql = "select id, username, password, status from auto_check where status=0;"
    rows = dao.execute_sql(sql)
    for row in rows:
        # 正常打卡
        user_id = row[0]
        username = row[1]
        password = row[2]
        url = "http://" + str(server_ip) + ":" + str(server_port) + "/new_fuck_it/" + str(username) + "/" + str(password) + "/" + str(token)
        response = requests.get(url)
        resp = response.text
        # 在首页提交数据后 状态会调整为0
        if str(resp) == "打卡成功":
            # 打卡成功
            sql = "update auto_check set status='1' where id='" + str(user_id) + "';"
            dao.execute_sql(sql)
            print(str(username) + "打卡成功")
        else:
            print(resp)
            # 打卡异常
            sql = "update auto_check set status='3' where id='" + str(user_id) + "';"
            dao.execute_sql(sql)
            # 将异常信息写入数据库
            # 这里需要记录一下 有很多次异常了 但是不知道为什么异常了
            sql = "insert into error_record values(default," + "'" + str(username) + "', '" + str(resp) + "', '" + str(time.strftime("%Y-%m-%d")) + "')"
            dao.execute_sql(sql)
        time.sleep(10)
    dao.close()


# 一人一token
# 打卡函数
def fuck_check():
    dao.connect(dao_url, dao_username, dao_password, dao_port)
    # 0-开启打卡 | 1-已经打卡 | 2-关闭打卡 | 3-打卡异常 (3时为不打卡)
    # 查询出所有状态为0的用户
    sql = "select id, username, password, status, deviceId from auto_check where status=0;"
    rows = dao.execute_sql(sql)
    # print(rows)
    for row in rows:
        # 正常打卡
        user_id = row[0]
        username = row[1]
        password = row[2]
        # 在flask服务上 会自动从服务器上获取 deviceId
        # deviceId = row[4]
        url = "http://" + str(server_ip) + ":" + str(server_port) + "/fuck_it/" + str(username) + "/" + str(password)
        response = requests.get(url)
        resp = response.text
        # 在首页提交数据后 状态会调整为0
        if str(resp) == "打卡成功":
            # 打卡成功
            # print(resp)
            sql = "update auto_check set status='1' where id='" + str(user_id) + "';"
            dao.execute_sql(sql)
            # print(str(username) + "打卡成功")
        else:
            # 打卡异常
            sql = "update auto_check set status='3' where id='" + str(user_id) + "';"
            dao.execute_sql(sql)
            # 将异常信息写入数据库
            # 这里需要记录一下 有很多次异常了 但是不知道为什么异常了
            # print(resp)
            sql = "insert into error_record values(default," + "'" + str(username) + "', '" + str(resp) + "', '" + str(time.strftime("%Y-%m-%d")) + "')"
            dao.execute_sql(sql)
        time.sleep(15)
    dao.close()

# 发送打卡报告
# 这块还不太行 看看怎么可以好看一些
def send_status():
    dao.connect(dao_url, dao_username, dao_password, dao_port)
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
        '<a href="http://' + str(server_ip) + ':' + str(server_port) + '/fuck_all"><button>点击查看所有打卡状况</button></a>'
    html_string = str(html_string) + \
	'<a href="http://' + str(server_ip) + ':' + str(server_port) + '/index"><button>点击进入打卡主页</button></a>'
    server_msg = "http://www.pushplus.plus/send?token=" + \
        str(pp_token) + "&title=打卡统计表&content=" + \
        str(html_string) + \
        "&template=html&topic=" + str(pp_group)
    dao.close()
    # 发送内容 推送至微信
    requests.get(url=server_msg)


# BlockingScheduler
scheduler = BlockingScheduler()

# date: 特定的时间点触发
# interval: 固定时间间隔触发
# cron: 在特定时间周期性地触发

scheduler.add_job(reset_status, 'cron', day_of_week='0-6', hour=int(reset_hour), minute=int(reset_minute))

# 一个token 多人打卡 ===> 不推荐
# scheduler.add_job(new_fuck, 'cron', day_of_week='0-6', hour=int(tik_hour), minute=int(tik_minute))

# 一人一个token
scheduler.add_job(fuck_check, 'cron', day_of_week='0-6', hour=int(tik_hour), minute=int(tik_minute))

# 发送报告
scheduler.add_job(send_status, 'cron', day_of_week='0-6', hour=int(push_hour), minute=int(push_minute))

print("========== 启动成功 ===========")
scheduler.start()
