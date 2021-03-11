from flask import Flask
from flask import render_template
from flask import redirect
from flask import request
from flask import make_response


import requests
import json
import re
import demjson
import random
import time
import base64

from model.conn import DataDao
from auto_token.campus import CampusCard

import configparser

# config
cfg = configparser.ConfigParser()
cfg.read("config.ini")

# flask
app = Flask(__name__)

# database
dao = DataDao()
dao_url = str(cfg.get("mysql", "HOST"))
dao_username = str(cfg.get("mysql", "USERNAME"))
dao_password = str(cfg.get("mysql", "PASSWORD"))
dao_port = str(cfg.get("mysql", "PORT"))

# 你flask启动的服务
server_ip = str(cfg.get("server", "SERVER_IP"))
server_port = str(cfg.get("server", "SERVER_PORT"))

# 定义一个可以用来打卡的全局token
active_token_string = ""

@app.route('/index')
def index():
    user_data = []
    return render_template('index.html', user_data=user_data)


# 获得token
@app.route('/token/<username>/<password>/<deviceId>')
def token(username=None, password=None, deviceId=None):
    if not username:
        error_string = "用户名不能为空"
        return render_template('error.html', error_string=error_string)
    if not password:
        error_string = "密码不能为空"
        return render_template('error.html', error_string=error_string)
    if not deviceId:
        error_string = "deviceId不能为空"
        return render_template('error.html', error_string=error_string)
    if str(deviceId) == "0":
        # 这里为了简化 之前如果登陆过 设备号填0就从服务器找
        dao.connect(dao_url, dao_username, dao_password, dao_port)
        sql = "select deviceId from auto_check where username='" + str(username) + "'"
        rows = dao.execute_sql(sql)
        dao.close()
        if str(rows[0][0]) == "None":
            error_string = "deviceId不能为空"
            return render_template('error.html', error_string=error_string)
        deviceId = rows[0][0]
    # 登录完美校园获得token等信息
    cc = CampusCard(username, password, deviceId)
    try:
        cc.get_main_info()
        token = str(cc.get_token())
    except Exception as e:
        return render_template('error.html', error_string=str(e))
    # 登录成功
    return redirect("/getData/" + str(token) + "/" + str(username) + "/" + str(password) + "/" + str(deviceId))

# 通过token从完美校园拿到打卡信息
@app.route('/getData/<token>/<username>/<password>/<deviceId>')
def getData(token=None, username=None, password=None, deviceId=None):
    if not token or not username or not password or not deviceId:
        error_string = "参数错误"
        return render_template('error.html', error_string=error_string)
    # 构造
    post_data = {"businessType": "epmpics", "jsonData": {"templateid": "pneumonia", "token": str(token)}, "method": "userComeApp"}
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json;charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Linux; Android 5.1.1; HUAWEI MLA-AL10 Build/HUAWEIMLA-AL10; wv) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile "
                              "Safari/537.36 Wanxiao/4.6.2"
    }
    url = "https://reportedh5.17wanxiao.com/sass/api/epmpics"
    # 发送请求 获取所有打卡的数据
    response = requests.post(url=url, data=json.dumps(post_data), headers=headers)
    data = response.text
    # 处理数据
    data = re.sub(" ", "", str(data))
    data = re.sub("\\\\", "", str(data))
    data = re.sub('"{', "{", str(data))
    data = re.sub('}"', "}", str(data))
    data = demjson.encode(data)
    data = demjson.decode(data)
    data = json.loads(data)
    try:
        data = data['data']
    except Exception as e:
        return render_template('error.html', error_string=str(e))
    #　==================================================
    # 公告 写一写注意事项
    declared_data = {}
    dao.connect(dao_url, dao_username, dao_password, dao_port)
    sql = "select * from declared"
    rows = dao.execute_sql(sql)

    # 这里更新下账号密码 防止用户修改密码后 导致完美和mysql不一致
    user_sql = "update auto_check set password='" + str(password) + "' where username='" + str(username) + "';"
    dao.execute_sql(user_sql)
    dao.close()
    # 公告为空是 会有异常
    try:
        declared_data['data'] = rows[0][1]
    except Exception:
        declared_data['data'] = "暂时没有公告"
    # 提交数据 需要的部分
    user_data = {}

    # 把devicedId也带上
    user_data['deviceId'] = str(deviceId)

    # 区域的信息
    # areaStr => {'province': '山东省', 'city': 'XX市'}
    user_data['areaStr'] = data['areaStr']
    # customerid => XXXX
    user_data['customerid'] = data['customerid']
    # deptStr => {'deptid': XXXX, 'text': 'XXXX'}
    user_data['deptStr'] = data['deptStr']
    # phonenum => XXXX
    user_data['phonenum'] = data['phonenum']
    # stuNo => XXXX
    user_data['stuNo'] = data['stuNo']
    # userid => XXXX
    user_data['userid'] = data['userid']
    # username => XXXX
    user_data['username'] = data['username']
    # token => XX-XX-XX-XX
    user_data['token'] = str(token)
    # 这个是用户的账号和密码
    # user_name
    user_data['user_name'] = str(username)
    # pass_word
    user_data['pass_word'] = str(password)
    # ==================================================
    # 要返回给前端的数据
    data_list = []
    # 打卡的数据
    form_data = data['cusTemplateRelations']
    for each in form_data:
        # 把值存到对象里
        item = {}
        item['decription'] = each['decription']
        item['propertyname'] = each['propertyname']
        item['value'] = each['value']
        if item['propertyname'] == "temperature":
            number = random.uniform(0.1, 0.9)
            item['value'] = 36.0 + float(round(number, 1))
        item['checkValues'] = each['checkValues']
        data_list.append(item)
    return render_template('getData.html', data_list=data_list, user_data=user_data, declared_data=declared_data)


# 保存数据
@app.route('/save_data/<username>/<password>/<deviceId>', methods=['POST'])
def save_data(username=None, password=None, deviceId=None):
    if not username:
        error_string = "用户名不能为空"
        return render_template('error.html', error_string=error_string)
    if not password:
        error_string = "密码不能为空"
        return render_template('error.html', error_string=error_string)
    # json_data
    json_data = {}
    # 在 XXXXXXXXX (我自己设定了一个分隔符)
    # 这个之前的参数都是放JsonData的
    # 这个之后都是放到大的json_data
    is_jsonData = True
    updatainfo = []
    if request.method == 'POST':
        for each in request.form:
            if str(each) == "XXXXXXXXX":
                is_jsonData = False
                continue
            if is_jsonData:
                item = {
                    "propertyname": str(each),
                    "value": str(request.form[each])
                }
                updatainfo.append(item)
            else:
                # 判断是否有括号
                is_json = re.findall("\{", request.form[each], re.S | re.M)
                if is_json:
                    _form_data = re.sub("'", '"', str(request.form[each]))
                    _data = json.loads(str(_form_data))
                    _json_data = {}
                    for _each in _data:
                        _json_data[_each] = _data[_each]
                    json_data[each] = _json_data
                else:
                    json_data[each] = request.form[each]
        json_data['reportdate'] = int(round(time.time() * 1000))
        json_data['deptid'] = json_data['deptStr']['deptid']
        json_data['source'] = "app"
        json_data['templateid'] = "pneumonia"
        json_data['updatainfo'] = updatainfo
        json_data["gpsType"] = 1

        # 合并前对areaStr进行特殊编辑
        json_data['areaStr'] = json.dumps(json_data['areaStr'], ensure_ascii=False)

        save_data = {
            "businessType": "epmpics",
            "method": "submitUpInfo",
            "jsonData": json_data
        }
        save_data = json.dumps(save_data, ensure_ascii=False)

        # 操作数据库
        # 对数据进行base64编码（存储的时候）
        save_data = str(base64.b64encode(bytes(save_data, 'utf-8')))
        save_data = re.sub("b'", "", str(save_data))
        save_data = re.sub("'", "", str(save_data))
        # 先判断该用户是否存在
        dao.connect(dao_url, dao_username, dao_password, dao_port)
        sql = "select * from auto_check where username='" + str(username) + "';"
        rows = dao.execute_sql(sql)
        # 说明用户之前没有数据
        # 现在是新增
        if str(rows) == "()":
            # print("----------------------------")
            sql = "insert into auto_check values(0,'" + str(username) + "', '" + str(password) + "', '" + str(save_data) + "', " + "'0'," + str(deviceId) + ");"
        # 否则是更新数据
        else:
            sql = "update auto_check set status=0, data='" + str(save_data) + "', password='" + str(password) + "', deviceId='" + str(deviceId) + "' where username='" + str(username) + "';"
        dao.execute_sql(sql)
        dao.close()
        return redirect("/get_my_data/" + str(username) + "/" + str(password) + "/" + str(deviceId))

# 从mysql读个人数据
@app.route('/get_my_data/<username>/<password>/<deviceId>')
def get_my_data(username=None, password=None, deviceId=None):
    if not username:
        error_string = "参数错误"
        return render_template('error.html', error_string=error_string)
    if not password:
        error_string = "参数错误"
        return render_template('error.html', error_string=error_string)
    # 公告 写一写注意事项
    declared_data = {}
    dao.connect(dao_url, dao_username, dao_password, dao_port)
    sql = "select * from declared"
    rows = dao.execute_sql(sql)
    # 公告为空时 会导致异常
    try:
        declared_data['data'] = rows[0][1]
    except Exception:
        declared_data['data'] = "暂时没有公告"
    sql = "select * from auto_check where username='" + str(username) + "' and password='" + str(password) + "';"
    rows = dao.execute_sql(sql)
    dao.close()
    # 用户的打卡数据
    try:
        # 这里如果用户本身没有保存过数据 那么获取就会为空
        # 而且会报错
        item = {}
        item['id'] = rows[0][0]
        item['username'] = rows[0][1]
        item['password'] = rows[0][2]
        item['data'] = rows[0][3]
        item['status'] = rows[0][4]
        item['deviceId'] = rows[0][5]
    except Exception:
        error_string = "数据库没数据 先点更新数据 就可以查看个人数据了"
        return render_template('error.html', error_string=error_string)
    return render_template('my_data.html', user_data=item, declared_data=declared_data)


@app.route('/update/<username>/<password>/<status>')
def update(username=None, password=None, status=None):
    if not username:
        error_string = "用户名不能为空"
        return render_template('error.html', error_string=error_string)
    if not password:
        error_string = "密码不能为空"
        return render_template('error.html', error_string=error_string)
    if not status:
        error_string = "状态不能为空"
        return render_template('error.html', error_string=error_string)
    dao.connect(dao_url, dao_username, dao_password, dao_port)
    sql = "update auto_check set status='" + str(status) + "' where username='" + str(username) + "' and password='" + str(password) + "';"
    dao.execute_sql(sql)
    dao.close()
    return redirect("/get_my_data/" + str(username) + "/" + str(password))


@app.route('/fuck_all')
def fuck_all():
    dao.connect(dao_url, dao_username, dao_password, dao_port)
    sql = "select * from auto_check"
    rows = dao.execute_sql(sql)
    dao.close()
    data_list = []
    for row in rows:
        item = {}
        # item['id'] = row[0]
        username = str(row[1])
        item['username'] = str(username[0:3]) + "****" + str(username[7:11])
        item['status'] = row[4]
        # 新增设备ID
        item['deviceId'] = row[5]
        data = base64.b64decode(row[3]).decode("utf-8")
        data = json.loads(data)
        data = data['jsonData']['username']
        item['data'] = data
        data_list.append(item)
    # data =json.dumps(data, ensure_ascii=False)
    return render_template('fuck_all.html', data_list=data_list)

# 激活token
@app.route('/active_token/<token>')
def active_token(token=None):
    if not token:
        error_string = "参数错误"
        return render_template('error.html', error_string=error_string)
    url = "https://reportedh5.17wanxiao.com/api/reported/generateProtocol?token=" + str(token)
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 5.1.1; HUAWEI MLA-AL10 Build/HUAWEIMLA-AL10; wv) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile "
                              "Safari/537.36 Wanxiao/4.6.2"
    }
    resp = requests.get(url=url, headers=headers)
    resp = resp.text
    resp = json.loads(resp)
    resp = resp['msg']
    return str(resp)

@app.route('/get_token/<username>/<password>')
def get_token(username=None, password=None):
    if not username:
        error_string = "用户名不能为空"
        return render_template('error.html', error_string=error_string)
    if not password:
        error_string = "密码不能为空"
        return render_template('error.html', error_string=error_string)
    # 先判断数据是否存在 没有必要先登录
    dao.connect(dao_url, dao_username, dao_password, dao_port)
    sql = "select * from auto_check where username='" + str(username) + "' and password='" + str(password) + "';"
    rows = dao.execute_sql(sql)
    dao.close()
    # 账号密码存在 下面开始获取token
    try:
        deviceId = str(rows[0][5])
    except Exception:
        error_string = "要先登录才能获取token"
        return render_template('error.html', error_string=error_string)
    # 走到这里 说明数据库里有数据
    try:
        cc = CampusCard(username, password, deviceId)
        cc.get_main_info()
    except Exception:
        return "CampusCard error"
    # 取到了token
    token = str(cc.get_token())
    # 激活token
    msg = active_token(token)
    if msg != "成功":
        return "active error"
    return str(token)

# new_fuck_it => 一人token 多人打卡
# fuck_it => 一人一个token打卡

# 一人token 多人打卡
@app.route('/new_fuck_it/<username>/<password>/<token>')
def new_fuck_it(username=None, password=None, token=None):
    if not username:
        error_string = "用户名不能为空"
        return render_template('error.html', error_string=error_string)
    if not password:
        error_string = "密码不能为空"
        return render_template('error.html', error_string=error_string)
    if not token:
        error_string = "token不能为空"
        return render_template('error.html', error_string=error_string)
    # 先判断数据是否存在 没有必要先登录
    dao.connect(dao_url, dao_username, dao_password, dao_port)
    sql = "select * from auto_check where username='" + str(username) + "' and password='" + str(password) + "';"
    rows = dao.execute_sql(sql)
    dao.close()
    try:
        data = base64.b64decode(rows[0][3]).decode("utf-8")
    except Exception:
        error_string = "要先登录 才能打卡"
        return render_template('error.html', error_string=error_string)
    # 取到数据 直接打卡
    # 提交数据
    url = 'https://reportedh5.17wanxiao.com/sass/api/epmpics'
    headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json;charset=utf-8",
            "origin": "https://reportedh5.17wanxiao.com",
            "content-length": "1679",
            "accept-language": "zh-cn",
            "User-Agent": "Mozilla/5.0 (Linux; Android 5.1.1; HUAWEI MLA-AL10 Build/HUAWEIMLA-AL10; wv) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile "
                              "Safari/537.36 Wanxiao/4.6.2"
    }
    dao.connect(dao_url, dao_username, dao_password, dao_port)
    try:
        data = json.loads(data)
        data['jsonData']['token'] = str(token)
        data['jsonData']['reportdate'] = int(round(time.time() * 1000))
        data =json.dumps(data)
        resp = requests.post(url, data=data, headers=headers)
        resp = resp.text
        html = demjson.encode(resp)
        json_data = demjson.decode(html)
        json_response = json.loads(json_data)
        msg = json_response['msg']
        code = json_response['code']
    except Exception:
        error_string = "data不正确 重新登录看看?"
        dao.close()
        return render_template('error.html', error_string=error_string)
    if msg == "成功" and code == "10000":
        sql = "update auto_check set status=1 where username='" + str(username) + "' and password='" + str(password) + "';" 
        dao.execute_sql(sql)
        dao.close()
        return "打卡成功"
    else:
        return "error"

# 一人一个token打卡
@app.route('/fuck_it/<username>/<password>')
def fuck_it(username=None, password=None):
    if not username:
        error_string = "用户名不能为空"
        return render_template('error.html', error_string=error_string)
    if not password:
        error_string = "密码不能为空"
        return render_template('error.html', error_string=error_string)
    # 先判断数据是否存在 没有必要先登录
    dao.connect(dao_url, dao_username, dao_password, dao_port)
    sql = "select * from auto_check where username='" + str(username) + "' and password='" + str(password) + "';"
    rows = dao.execute_sql(sql)
    dao.close()
    try:
        data = base64.b64decode(rows[0][3]).decode("utf-8")
        deviceId = str(rows[0][5])
    except Exception:
        error_string = "要先登录 才能打卡 重新登录看看?"
        return render_template('error.html', error_string=error_string)
    # 走到这里 说明数据库里有数据
    try:
        cc = CampusCard(username, password, deviceId)
        cc.get_main_info()
    except Exception:
        error_string = "CampusCard()获取token出现错误"
        return render_template('error.html', error_string=error_string)
    # 取到了token
    token = str(cc.get_token())
    # 激活token
    msg = active_token(token)
    '''
    if msg != "成功":
        error_string = "token激活失败"
        return render_template('error.html', error_string=error_string)
    '''
    # 这里已经激活token
    # 提交数据
    url = 'https://reportedh5.17wanxiao.com/sass/api/epmpics'
    headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json;charset=utf-8",
            "origin": "https://reportedh5.17wanxiao.com",
            "content-length": "1679",
            "accept-language": "zh-cn",
            "User-Agent": "Mozilla/5.0 (Linux; Android 5.1.1; HUAWEI MLA-AL10 Build/HUAWEIMLA-AL10; wv) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile "
                              "Safari/537.36 Wanxiao/4.6.2",
    }
    dao.connect(dao_url, dao_username, dao_password, dao_port)
    try:
        data = json.loads(data)
        data['jsonData']['token'] = str(token)
        data['jsonData']['reportdate'] = int(round(time.time() * 1000))
        data =json.dumps(data)
        resp = requests.post(url, data=data, headers=headers)
        resp = resp.text
        html = demjson.encode(resp)
        json_data = demjson.decode(html)
        json_response = json.loads(json_data)
        msg = json_response['msg']
        code = json_response['code']
    except Exception:
        error_string = "data不正确 重新登录看看?"
        dao.close()
        return render_template('error.html', error_string=error_string)
    if msg == "成功" and code == "10000":
        sql = "update auto_check set status=1 where username='" + str(username) + "' and password='" + str(password) + "';" 
        dao.execute_sql(sql)
        dao.close()
        return "打卡成功"
    else:
        return "error"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=str(server_port), debug=False)


# 收尾
print("程序运行结束")
dao.close()
print("断开数据库连接")
