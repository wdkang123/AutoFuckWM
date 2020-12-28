# 完美校园自动打卡 - autofuck
:blush: 黄海学院 - 完美校园自动打卡
<br />
<br />
:star: 限于简化日常烦躁打卡
<br />
<br />
:eyes: 身体如果出现异常 一定要及时的汇报学校!
<br />
<br />
:earth_asia: 希望大家健健康康平平安安度过疫情！
<br />
<br />
:bell: 保佑大家

:smiley: 输入账号密码登录(这里会到完美校园去验证是否正确)
<br />
![](https://github.com/wdkang123/AutoFuckWM/blob/main/images/img1.png?raw=true)
<br />
<br />
:smiley: 接着获取当前需要打卡的信息(这里填写之后 保存会存到数据库中 当下次如果有更新内容 再次登录填写即可)
<br />
![](https://github.com/wdkang123/AutoFuckWM/blob/main/images/img2.png?raw=true)
<br />
<br />
:smiley: 可以查看自己的打卡状态
<br />
![](https://github.com/wdkang123/AutoFuckWM/blob/main/images/img3.png?raw=true)
<br />

# 目录

# 1.基本环境需求

json 解析json数据 和 提交json数据 

demjson 同json

re 正则模块

requests 发送get post请求 获取数据

time 时延

datetime 时间戳

configparser 解析config.ini

apscheduler 负责定时任务 定时打卡

flask 主模块 提供web服务

random 随机函数

base64 把保存的数据转换为base64存储到数据库中

pymysql 连接mysql

hashlib hash运算

urllib3 url编码相关

Crypto 加密解密（计算token）



# 2.部署方法

前提你有个服务器

填写config.ini 确保填写无误

在服务器上以后台方式启动main.py 和 tik_tok_fuck.py即可

访问链接为: http://xxx.xxx:8086/index (登录 需要完美校园的账号密码)

接着填写相关信息并保存

tik_tok_fuck.py会定时将保存到数据库中的数据进行提交 以完成打卡

（其余相关的信息 可以查看 main.py中的app.route留出的接口）

这些接口可以自己二次开发 

tik_tok_fuck 只不过是定时的通过requests调用main中的签到函数罢了


# 感谢:

吃水不忘挖井人 感谢大家的无私贡献!

在此对项目开源的大家表示感谢!



感谢 [zhongbr](https://github.com/zhongbr)/**[wanmei_campus](https://github.com/zhongbr/wanmei_campus)**

这里的登录校验、token计算 都是zhongbr提供的模块



感谢 [YooKing](https://github.com/YooKing)/**[HAUT_autoCheck](https://github.com/YooKing/HAUT_autoCheck)**

这里的思路设计参考了一部分



感谢 [Tishacy](https://github.com/Tishacy)/**[ZJU-nCov-Hitcarder](https://github.com/Tishacy/ZJU-nCov-Hitcarder)**

思路上也参考了一部分



# 最后

最后 希望大家身体健康 平平安安！
