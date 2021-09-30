# -*- encoding:utf-8 -*-
import requests
import json
import os
import utils
from urllib.parse import urlencode

class WoZaiXiaoYuanPuncher:
    def __init__(self):
        # JWSESSION
        self.jwsession = None
        # 签到ID
        self.signid = None
        # 签到登录ID
        self.signlogId = None
        # 签到结果
        self.status_code = 0
        # 登陆接口
        self.loginUrl = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username"
        # 请求头
        self.header = {
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat",
            "Content-Type": "application/json;charset=UTF-8",
            "Content-Length": "2",
            "Host": "gw.wozaixiaoyuan.com",
            "Accept-Language": "en-us,en",
            "Accept": "application/json, text/plain, */*"
        }
        # 请求体（必须有）
        self.body = "{}"

    # 登录
    def login(self):
        username, password = str(os.environ['WZXY_USERNAME']), str(os.environ['WZXY_PASSWORD'])
        url = f'{self.loginUrl}?username={username}&password={password}' 
        self.session = requests.session()
        # 登录
        response = self.session.post(url=url, data=self.body, headers=self.header)
        res = json.loads(response.text)
        if res["code"] == 0:
            print("使用账号信息登录成功")
            jwsession = response.headers['JWSESSION']
            self.setJwsession(jwsession)
            return True
        else:
            print(res)
            print("登录失败，请检查账号信息")
            self.status_code = 5
            return False

    # 设置JWSESSION
    def setJwsession(self, jwsession):
        # 如果找不到cache,新建cache储存目录与文件
        if not os.path.exists('.cache'): 
            print("正在创建cache储存目录与文件...")
            os.mkdir('.cache')
            data = {"jwsession":jwsession}
        elif not os.path.exists('.cache/cache.json'):
            print("正在创建cache文件...")
            data = {"jwsession":jwsession}
        # 如果找到cache,读取cache并更新jwsession
        else:
            print("找到cache文件，正在更新cache中的jwsession...")
            data = utils.processJson('.cache/cache.json').read()
            for item in data:
                item['jwsession'] = jwsession                 
        utils.processJson(".cache/cache.json").write(data)
        self.jwsession = data['jwsession']  
    
    # 获取JWSESSION
    def getJwsession(self):
        if not self.jwsession:  # 读取cache中的配置文件
            data = utils.processJson(".cache/cache.json").read()
            self.jwsession = data['jwsession']  
        return self.jwsession

    # 获取签到列表，判断当前签到时间段与签到情况，符合条件则自动进行签到
    def PunchIn(self):
        print("获取签到列表中...")
        url = "https://student.wozaixiaoyuan.com/sign/getSignMessage.json"
        self.header['Host'] = "student.wozaixiaoyuan.com"
        self.header['Content-Type'] = "application/x-www-form-urlencoded"
        self.header['JWSESSION'] = self.getJwsession()
        sim_data = {
            "page": 1,
            "size": 5
        }
        data = urlencode(sim_data)
        self.session = requests.session()    
        response = self.session.post(url=url, data=data, headers=self.header)
        res = json.loads(response.text)
        # 如果 jwsession 无效，则重新 登录 + 签到
        if res['code'] == -10:
            print('jwsession 无效，将尝试使用账号信息重新登录')
            self.status_code = 4
            loginStatus = self.login()
            if loginStatus:
                self.PunchIn()
            else:
                print("重新登录失败，请检查账号信息")
        elif res['code'] == 0:                    
            # 标志时段是否有效
            inSeq = False
            # 遍历每个签到时段（不同学校的签到时段数量可能不一样）
            for i in res['data']:
                # 判断时段是否有效
                if int(i['state']) == 1:
                    inSeq = True
                    # 判断是否已经签到
                    if int(i['type']) == 1:
                        self.doPunchIn(str(i['id']),str(i['logId']))
                    elif int(i['type']) == 0:
                        self.status_code = 2
                        print("已经签过到了")
                elif int(i['state'])==2:
                    print("未在时间段！")
            # 如果当前时间不在任何一个签到时段内
            if inSeq == False:            
                self.status_code = 3
                print("签到失败：不在签到时间段内")

    # 执行签到
    # 参数signid：当前签到的signId值。signlogId：当前签到的id值
    def doPunchIn(self,signid,signlogId):
        print("正在测试签到...")
        url = "https://student.wozaixiaoyuan.com/sign/doSign.json"
        self.header['Host'] = "student.wozaixiaoyuan.com"
        self.header['Content-Type'] = "application/json"
        self.header['JWSESSION'] = self.getJwsession()
        sign_data = {
            "id": str(signlogId),
            "signId": str(signid),
            "latitude": os.environ['WZXY_LATITUDE'],
            "longitude": os.environ['WZXY_LONGITUDE'],
            "country": os.environ['WZXY_COUNTRY'],
            "province": os.environ['WZXY_PROVINCE'],
            "city": os.environ['WZXY_CITY'],
            "district": os.environ['WZXY_DISTRICT'],
            "township": os.environ['WZXY_TOWNSHIP']
        }
        data_json = json.dumps(sign_data)
        # requests库提交数据进行post请求
        req = requests.post(url=url, data=data_json, headers=self.header)
        # 打印Unicode编码格式的json数据
        req=json.loads(req.text)
        if req["code"] == 0:
            self.status_code = 1
            print("签到成功")
        else:
            print(response)
            print("签到失败")

    # 获取签到结果
    def getResult(self):
        res = self.status_code
        if res == 1:
            return "✅ 签到成功"
        elif res == 2:
            return "✅ 你已经签过到了，无需重复签到"
        elif res == 3:
            return "❌ 签到失败，当前不在签到时间段内"
        elif res == 4:
            return "❌ 签到失败，jwsession 无效"            
        elif res == 5:
            return "❌ 签到失败，登录错误，请检查账号信息"
        else:
            return "❌ 签到失败，发生未知错误，请检查日志"

    # 推送签到结果
    def sendNotification(self):
        notifyTime = utils.getCurrentTime()
        notifyResult = self.getResult()

        if os.environ.get('SCT_KEY'):
            # serverchan 推送
            notifyToken = os.environ['SCT_KEY']
            url = "https://sctapi.ftqq.com/{}.send"
            body = {
                "title": "⏰ 我在校园签到结果[M]：{}".format(notifyResult),
                "desp": "签到项目：点名签到\n\n签到情况：{}\n\n签到时间：{}".format(notifyResult, notifyTime)
            }
            requests.post(url.format(notifyToken), data=body)
            print("消息经Serverchan-Turbo推送成功")
        if os.environ.get('PUSHPLUS_TOKEN'):
            # pushplus 推送
            url = 'http://www.pushplus.plus/send'
            notifyToken = os.environ['PUSHPLUS_TOKEN']
            content = json.dumps({
                "签到项目": "点名签到",
                "签到情况": notifyResult,
                "签到时间": notifyTime
            }, ensure_ascii=False)
            msg = {
                "token": notifyToken,
                "title": "⏰ 我在校园签到结果通知",
                "content": content,
                "template": "json"
            }
            requests.post(url, data=msg)
            print("消息经pushplus推送成功")
        if os.environ.get('BARK_TOKEN'):
            # bark 推送
            notifyToken = os.environ['BARK_TOKEN']
            req = "{}/{}/{}".format(notifyToken, "⏰ 我在校园签到（点名签到）结果通知", notifyResult)
            requests.get(req)
            print("消息经bark推送成功")


if __name__ == '__main__':
    # 找不到cache，登录+签到
    wzxy = WoZaiXiaoYuanPuncher()
    if not os.path.exists('.cache'):
        print("找不到cache文件，正在使用账号信息登录...")
        loginStatus = wzxy.login()
        if loginStatus:
            wzxy.PunchIn()
        else:
            print("登陆失败，请检查账号信息")
    else:
        print("找到cache文件，尝试使用jwsession签到...")
        wzxy.PunchIn()
    wzxy.sendNotification()

