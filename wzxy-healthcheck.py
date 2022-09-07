# -*- encoding:utf-8 -*-
import base64
import hashlib
import hmac
import json
import os
import time
import urllib
import urllib.parse
from urllib.parse import urlencode
import requests
import utils


class WoZaiXiaoYuanPuncher:
    def __init__(self):
        # JWSESSION
        self.jwsession = None
        #打卡id
        self.check_id = None
        #打卡名称
        self.check_title = None
        # 打卡时段
        self.seq = None
        # 打卡结果
        self.status_code = 0
        # 登陆接口
        self.loginUrl = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username"
        # 请求头
        self.header = {
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.13(0x18000d32) NetType/WIFI Language/zh_CN miniProgram",
            "Content-Type": "application/json;charset=UTF-8",
            "Content-Length": "2",
            "Host": "gw.wozaixiaoyuan.com",
            "Accept-Language": "en-us,en",
            "Accept": "application/json, text/plain, */*",
        }
        # 请求体（必须有）
        self.body = "{}"

    # 登录
    def login(self):
        username, password = str(os.environ["WZXY_USERNAME"]), str(
            os.environ["WZXY_PASSWORD"]
        )
        url = f"{self.loginUrl}?username={username}&password={password}" 
        self.session = requests.session()
        # 登录
        response = self.session.post(url=url, data=self.body, headers=self.header)
        res = json.loads(response.text)
        if res["code"] == 0:
            print("使用账号信息登录成功")
            jwsession = response.headers["JWSESSION"]
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
        if not os.path.exists(".cache"): 
            print("正在创建cache储存目录与文件...")
            os.mkdir(".cache")
            data = {"jwsession": jwsession}
        elif not os.path.exists(".cache/cache.json"):
            print("正在创建cache文件...")
            data = {"jwsession": jwsession}
        # 如果找到cache,读取cache并更新jwsession
        else:
            print("找到cache文件，正在更新cache中的jwsession...")
            data = utils.processJson(".cache/cache.json").read()
            data["jwsession"] = jwsession                 
        utils.processJson(".cache/cache.json").write(data)
        self.jwsession = data["jwsession"]  
    
    # 获取JWSESSION
    def getJwsession(self):
        if not self.jwsession:  # 读取cache中的配置文件
            data = utils.processJson(".cache/cache.json").read()
            self.jwsession = data["jwsession"]  
        return self.jwsession

    # 获取打卡列表，判断当前打卡时间段与打卡情况，符合条件则自动进行打卡
    def PunchIn(self):
        print("获取打卡列表中...")
        url = "https://gw.wozaixiaoyuan.com/health/mobile/health/getBatch"
        self.header["Host"] = "gw.wozaixiaoyuan.com"
        self.header["Content-Type"] = "application/json;charset=UTF-8"
        self.header["JWSESSION"] = self.getJwsession()
        self.session = requests.session()
        response = self.session.post(url=url, data=self.body, headers=self.header)
        res = json.loads(response.text)
        print(res)
        # 如果 jwsession 无效，则重新 登录 + 打卡
        if res["code"] == -10:
            print(res)
            print("jwsession 无效，将尝试使用账号信息重新登录")
            self.status_code = 4
            loginStatus = self.login()
            if loginStatus:
                self.PunchIn()
            else:
                print(res)
                print("重新登录失败，请检查账号信息")     
        elif res["code"] == 0:                    
            # 标志时段是否有效
            inSeq = False
            # 遍历每个打卡时段（不同学校的打卡时段数量可能不一样）
            data1 = res["data"]
            for i in data1["list"]:
                # 判断时段是否有效
                if int(i["state"]) == 1:
                    inSeq = True
                    # 保存当前学校的打卡时段
                    self.check_id = str(i["id"])
                    self.check_title = str(i["title"])
                    # 判断是否已经打卡
                    if int(i["type"]) == 0:
                        self.doPunchIn(str(i["id"]),str(i["title"]))
                    elif int(i["type"]) == 1:
                        self.status_code = 2
                        print("已经打过卡了")
            # 如果当前时间不在任何一个打卡时段内
            if inSeq == False:            
                self.status_code = 3
                print("打卡失败：不在打卡时间段内")

    # 执行打卡
    # 参数seq ： 当前打卡的序号
    def doPunchIn(self, check_id, check_title):
        print("正在进行：" + self.check_title + "...")
        url = "https://gw.wozaixiaoyuan.com/health/mobile/health/save?batch=" + self.check_id
        self.header["Host"] = "gw.wozaixiaoyuan.com"
        self.header["Content-Type"] = "application/json;charset=UTF-8"
        self.header["Content-Length"] = 158
        self.header["Origin"] = "https://gw.wozaixiaoyuan.com"
        self.header["X-Requested-With"] = "com.tencent.mm"
        self.header["Sec-Fetch-Site"] = "same-origin"
        self.header["Sec-Fetch-Mode"] = "cors"
        self.header["Sec-Fetch-Dest"] = "empty"
        self.header["Referer"] = "https://gw.wozaixiaoyuan.com/h5/mobile/health/index/health/detail?id=" + self.check_id
        self.header["Cookie"] = "JWSESSION=" + self.getJwsession()
        self.header["JWSESSION"] = self.getJwsession()

        # cur_time = int(round(time.time() * 1000))
        
        # if os.environ["WZXY_TEMPERATURE"]:
        #     TEMPERATURE = utils.getRandomTemperature(os.environ["WZXY_TEMPERATURE"])
        # else:
        #     TEMPERATURE = utils.getRandomTemperature("36.0~36.5")
        sign_data = {
            "location": "中国/陕西省/宝鸡市/岐山县/蔡家坡镇//156/610323/156610300/610323112",
            "t1": "是",
            "t2": "绿色",
            "t3": "是",
            "type": 0,
            "locationType": 0
        }
        data = urlencode(sign_data)
        self.session = requests.session()    
        response = self.session.post(url=url, data=sign_data, headers=self.header)
        response = json.loads(response.text)
        print(response)
        # 打卡情况
        if response["code"] == 0:
            self.status_code = 1
            print("打卡成功")
        else:
            print(response)
            print("打卡失败")
                
    # 获取打卡时段
    def getSeq(self):
        seq = self.seq
        if seq == 1:
            return "早打卡"
        elif seq == 2:
            return "午打卡"
        elif seq == 3:
            return "晚打卡"
        else:
            return "非打卡时段"
    
    # 获取打卡结果
    def getResult(self):
        res = self.status_code
        if res == 1:
            return "✅ 打卡成功"
        elif res == 2:
            return "✅ 你已经打过卡了，无需重复打卡"
        elif res == 3:
            return "❌ 打卡失败，当前不在打卡时间段内"
        elif res == 4:
            return "❌ 打卡失败，jwsession 无效"            
        elif res == 5:
            return "❌ 打卡失败，登录错误，请检查账号信息"
        else:
            return "❌ 打卡失败，发生未知错误，请检查日志"

    # 推送打卡结果
    def sendNotification(self):
        notifyTime = utils.getCurrentTime()
        notifyResult = self.getResult()
        notifySeq = self.getSeq()

        if os.environ.get("PUSHPLUS_TOKEN"):
            # pushplus 推送
            url = "http://www.pushplus.plus/send"
            notifyToken = os.environ["PUSHPLUS_TOKEN"]
            content = json.dumps(
            {
                "打卡项目": "日检日报",
                "打卡情况": notifyResult,
                "打卡时段": notifySeq,
                "打卡时间": notifyTime,
            },
            ensure_ascii=False,
            )
            msg = {
                "token": notifyToken,
                "title": "⏰ 我在校园打卡结果:{}".format(notifyResult),
                "content": content,
                "template": "json",
            }
            body = json.dumps(msg).encode(encoding="utf-8")
            headers = {"Content-Type": "application/json"}
            r = requests.post(url, data=body, headers=headers).json()
            if r["code"] == 200:
                print("消息经 pushplus 推送成功")
            else:
                print("pushplus: " + str(r["code"]) + ": " + str(r["msg"]))
                print("消息经 pushplus 推送失败，请检查错误信息")

if __name__ == "__main__":
    # 找不到cache，登录+打卡
    wzxy = WoZaiXiaoYuanPuncher()
    if not os.path.exists(".cache"):
        print("找不到cache文件，正在使用账号信息登录...")
        loginStatus = wzxy.login()
        if loginStatus:
            wzxy.PunchIn()
        else:
            print("登陆失败，请检查账号信息")
    else:
        print("找到cache文件，尝试使用jwsession打卡...")
        wzxy.PunchIn()
    wzxy.sendNotification()