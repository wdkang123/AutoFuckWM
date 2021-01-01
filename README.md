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

python3的环境

mysql的对外服务

开放了8086端口（可以在main.py中进行修改）

下面为需要安装的Python库:

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

2.1 前提有个服务器（开放了8086端口）并将数据库搭建起来

2.2 填写config.ini （里边是配置相关的东西）

2.3 在服务器上以后台方式启动main.py 和 tik_tok_fuck.py即可

`nohup ./main.py &`

`nohup ./tik_tok_fuck.py &`

2.4 访问链接为: http://服务器IP地址:8086/index (登录 需要完美校园的账号密码)

2.5 填写打卡相关的信息并保存

完工！



# 3.文件目录说明

config.ini - 配置文件

main.py - flask的主函数 程序的主核心 提供web服务 数据库操作服务

tik_tok_fuck.py - 调用flask的服务 定时完成一些任务

MySqlConn.py - 简单的封装了一下mysql

templates 目录 - 存放web模板

static 目录 - 静态资源 用了layUI 主要web页面简单 就随手胡了一个

images 目录 - 图片目录 其实和项目没啥关系

database目录 - 里边是程序运行需要的库 自己导入进去

auto_token 目录 [YooKing](https://github.com/YooKing)/**[HAUT_autoCheck](https://github.com/YooKing/HAUT_autoCheck)** 从这里删删改改过来的



# 4.整体代码逻辑

## 4.1 main.py提供的路由接口：

1 `/index` 主要用于渲染主页面

2 `/token/<username>/<password>` 通过账号密码进行获取token 结果会被重定向到`/getData/<token>/<username>/<password>`

3 `/getData/<token>/<username>/<password>`  获取用户打卡的内容 并取回上次打卡的信息（如果完美校园的服务器有保存的话） 类似上次打卡地址等信息

最后会转到 `getData.html` 页面 也就是登录后填写打卡数据的页面

4 `/active_token/<token>` 拿到的token并不能打卡 这里做的激活token

5 `/save_data/<username>/<password>` 保存用户的打卡数据到mysql（为以后自动打卡提供数据支持）

6 `/get_my_data/<username>/<password>` 个人数据 最后转到 `my_data.html` （这里有一些 开启打卡、立即打卡、关闭打卡等功能）

7 `/update/<username>/<password>/<status>` 更新用户的打卡数据

8 `/fuck_all` 查看所有用户的打卡数据 （这个设计感觉不好）我主要是为了帮忙看 大家是否打卡异常 

用的时候 注意这个打卡接口 可能会泄露大家的个人信息 所以如果公开服务器的话 尽量干掉这个接口吧 如果是朋友们一起用 那可以留着

9 `/fuck_it/<username>/<password>` 打卡的核心函数 通过账号密码 得到token 接着激活token 从mysql中取到上次打卡的数据 提交给完美校园 完成自动打卡



## 4.2 tik_tok_fuck.py 干了什么

通过调度器 定时的执行一些任务

`scheduler.add_job(reset_status, 'cron', *day_of_week*='0-6', *hour*=21, *minute*=15)`

`scheduler.add_job(fuck_check, 'cron', *day_of_week*='0-6', *hour*=5, *minute*=30)`

`scheduler.add_job(send_status, 'cron', *day_of_week*='0-6', *hour*=8, *minute*=15)`



reset_status 是将打卡的状态为1的用户调整为0 以供第二天打卡

 fuck_check 是将所有状态为0的人进行自动打卡

send_status 是发送打卡结果的微信通知（这里用的是pushplus）



# 5.状态为0、1、2的说明

状态为0  表示第二天正常打卡

状态为1 表示已经帮你自动打卡了

状态为2 表示你关闭了自动打卡（数据留着 但是不会帮你打卡）

状态为3 表示打卡异常（这个时候是没有打卡的 要注意）




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
