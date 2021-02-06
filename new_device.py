from auto_token.campus_device import LoginBySMS

# 此脚本用于验证虚拟设备
# device_seed输入任意数字
# 密码登陆时需传入相同的device seed

print('username:', end="")
username = input()
print('device seed:', end="")
device_seed = input()

t = LoginBySMS(username, device_seed)
print(t.sendSMS())

print('SMS code:', end="")
sms = input()
print(t.authSMS(sms))

print("deviceId: %s" % t.get_device())
