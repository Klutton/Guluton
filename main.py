import copy
import socket
import datetime
#import time
import json as json_
import os
#import asyncio
import requests
import re
#import random
import sys
import MsgRender
import AlarmBroadcast
import NeteaseMusicCrawler
import NeteaseMusicCrawler as MC
#from selenium import webdriver


#######################################################################
#初始化监听端口
ListenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#初始化响应头
HttpResponseHeader = 'HTTP/1.1 200 OK\r\n'
HttpResponseHeader += 'Content-Type:text/html\r\n'
HttpResponseHeader += '\r\n'
HttpResponseHeader += '<h1>hi, Guluton!</h1>'
#######################################################################

class Config:
    listenip = '127.0.0.1'
    listenport = 5701
    sendip = '127.0.0.1'
    sendport = 5700
    groupposition = ''
    dictposition = ''
    importposition = ''
    cookieposition = ''
    alarmposition = ''
    timetableposition = ''

def set_up():
    config = IO.dict_reader(IO, 'config.json')
    Config.listenip = config['listenip']
    Config.listenport = config['listenport']
    Config.sendip = config['sendip']
    Config.sendport = config['sendport']
    Config.groupposition = config['groupposition']
    Config.dictposition = config['dictposition']
    Config.importposition = config['importposition']
    Config.cookieposition = config['cookieposition']
    Config.alarmposition = config['alarmposition']
    Config.timetableposition = config['timetableposition']
    Secure.admin = config['admin_id']
    Secure.bot = config['bot_id']

    sys.path.append(Config.importposition)
    # Secure.code = Secure.secure_code_generate(Secure, 32)
    # os.system('"C:\\Users\86153\Desktop\q-robot\go-cqhttp_windows_386.exe"')
    ListenSocket.bind((Config.listenip, Config.listenport))
    ListenSocket.listen(100)
    print(f"**********************\n已经设置监听socket位于 {Config.listenip}:{Config.listenport}")
    print("用于接收消息\n**********************")
    Dicts.dict_searcher(Dicts, Config.dictposition)
    print("====")
    MusicUserLogin.get_cookie(MusicUserLogin, Config.cookieposition)
    NeteaseMusicCrawler.add_cookie(MusicUserLogin.cookie)
    print('====')
    Groups.group = IO.dict_reader(IO, Config.groupposition)
    print('已加载组\n====')
    AlarmBroadcast.alarm_setup(Config.alarmposition)
    print('已初始化Alarm\n====')
    MsgRender.set_up(Config.timetableposition)
    print('已初始化Render\n====')
    return

class Groups:
    group = {}

#方便读取各种字典
class IO:

    def dict_reader(self,fileposition):
        with open(fileposition, 'r', encoding='utf-8') as fr:
            result = json_.loads(fr.read())
        print(f"载入位于{fileposition}")
        return result

    def dict_writer(self,fileposition,new_dict):
        with open(fileposition, 'w', encoding='utf-8') as fr:
            fr.write(json_.dumps(new_dict, ensure_ascii = False, indent=4))
        print(f"写入位于{fileposition}")
        return

#自动读取本地字典并存入内存
class Dicts:
    dictlist = {}
    lists = []
    #file为字典所在的文件夹路径
    def dict_searcher(self, file):
        print("搜索并载入字典中")
        list = os.listdir(file)
        Dicts.lists = list
        print("字典列表：",list)
        for i in range(0,len(list)):
            filename = file + '/' + list[i]
            #注意转义一下哦
            with open(filename, 'r', encoding='utf-8') as fr:
                Dicts.add_dict(Dicts, list[i] ,json_.loads(fr.read()))
            print("已载入",list[i])
            #print("字典列表",Dicts.dictlist)
        return

    def add_dict(self, dictname, dictcontent):
        Dicts.dictlist[dictname] = dictcontent
        return True

class MusicUserLogin:
    cookie = {}
    #加载本地cookie登录到selenium
    def get_cookie(self,path):
        print("搜索并载入网易云音乐用户")
        #注意转义一下哦
        with open(path, 'r', encoding='utf-8') as fr:
            MusicUserLogin.cookie = json_.loads(fr.read())
        #print(MusicUserLogin.cookie)
        #print(type(MusicUserLogin.cookie))
        print("已载入", path)

#返回类型：dict
#接收消息
class RecvMsg:
    def request_to_json(msg):#检测request里是否有json消息
        for i in range(len(msg)):
            if msg[i] == "{" and msg[-2] == "}":#寻找大括号，返回json
                return json_.loads(msg[i:])

        print("**********************\nError: 接收到的信息中无json\n**********************")
        return #如果没找到json，报错直接return

    def msg_rec(self):
        conn, Address = ListenSocket.accept()
        Request = conn.recv(4096).decode(encoding='utf-8')
        #print("New Request:\n", Request, sep="")
        rev_json = self.request_to_json(Request)
        #print("rev_json:\n", rev_json, "\n", "-"*20,  sep="")

        conn.sendall((HttpResponseHeader).encode(encoding='utf-8'))
        conn.close()
        return rev_json

#发送信息
class SendMsg:
    def msg_sender(self, dict , param):
        send = requests.post(url=f"http://{Config.sendip}:{Config.sendport}"+param , json=dict)
        response = json_.loads(send.text)
        if response["retcode"] == 0 and response["status"] == "ok":
            log =  "##发送消息\n返回码：" + str(response["retcode"])
            try:
                log += "\n++++++++\n消息内容：\n" + dict["message"] + "\n++++++++"
            except:
                print('未返回消息内容')
            RecvHandler.log_sender(RecvHandler, log)
            RecvHandler.log_sender(RecvHandler, "确认信息已发送\n")
            return response
        else:
            RecvHandler.log_sender(RecvHandler, f"Error：信息已发送，但不一定成功，返回码来自{Config.sendip}:{Config.sendport}\n")
            error = str(response["retcode"]) + " " + response["status"]+ " " + response["wording"]
            RecvHandler.log_sender(RecvHandler, error)
            RecvHandler.log_sender(RecvHandler, response)
            return

#处理接收消息的类型
class RecvHandler:
    counter = 0#计数心跳包
    def main_handler(self,json):
        #首先读取并输出时间和qq号
        #判断消息类型
        #元事件
        if json["post_type"] == "meta_event":
            # 当接收到元事件类型为心跳包
            if json["meta_event_type"] == "heartbeat":
                RecvHandler.counter+=1#心跳包数量增加
                #print(RecvHandler.counter)
                if RecvHandler.counter == 30:#当心跳包攒到一百个
                    RecvHandler.log_sender(RecvHandler, "log_head")#发送日志
                    RecvHandler.log_sender(RecvHandler, "元事件：已接收30个心跳包")
                    RecvHandler.log_sender(RecvHandler, "log_end")
                    RecvHandler.counter=0#计数器归零
            # 当接收到元事件类型为生命周期，不知道里面有啥
            elif json["meta_event_type"] == "lifecycle":
                RecvHandler.log_sender(RecvHandler, "log_head")
                RecvHandler.log_sender(RecvHandler, "元事件：生命周期")  # 发送日志
                RecvHandler.log_sender(RecvHandler, json)
                RecvHandler.log_sender(RecvHandler, "log_end")
        #消息
        elif json["post_type"] == "message":
            RecvHandler.msg_handler(RecvHandler, json)
        return

    #消息类型处理
    def msg_handler(self,json):
        #关键词检索：先判断群聊或私聊
        payload = {}
        #好友私聊
        if json["sub_type"] == "friend":
            RecvHandler.log_sender(RecvHandler, "log_head")
            payload["user_id"] = json["user_id"]  # 默认发送给发消息者
            param = "/send_private_msg"
            #测试用
            if json["raw_message"] == "测试":
                payload["message"] = "你好吖"
                SendMsg.msg_sender(SendMsg, payload ,param)
            elif json['raw_message'] == '重新载入':
                set_up()
                payload["message"] = "重载完毕"
                SendMsg.msg_sender(SendMsg, payload ,param)
            elif json["raw_message"] == "帮助":
                payload["message"] = "你好，我是Guluton，关键词：\n测试\n仪表盘（需要令牌）\nalarm"
                return SendMsg.msg_sender(SendMsg  , payload , param)
            elif json['raw_message'] == 'alarm':
                #(1天/周后) 17:00(:30) 每周1,2,3/每2天 (小睡100,200,300) (名字：啦啦啦) (速速起床 某某图片)
                payload["message"] = "中括号内为注释，括号内为非必选，括号不用加，注意区分中英文字符，空格，逗号等\n" \
                                     "嗨，下面是闹钟相关用法：\n#1、设置一个闹钟：\n" \
                                     "闹钟+(1天/周后【不写默认当天】)空格17:30(:30【注意为英文冒号，秒不填默认为00】)空格" \
                                     "(每周1,2,3/每1天【注意为数字和英文逗号，不填默认只响一次】)" \
                                     "空格(小睡100,200,300【不填默认没有，十位数和个位数为秒数，百位数以上为分钟数，不能超过30分钟59秒】)空格" \
                                     "(名字：啦啦啦【注意为中文冒号，不加默认为”一个闹钟“】)空格(叫你时候发送的信息，用空格隔开)\n" \
                                     "注：时间后面的几个可选附加条件顺序不是固定的，建议把叫你时候发送的信息放在后面；空格要加，不管加几个反正要加" \
                                     "\n#2、发送你创建的闹钟以及相关信息：\n查询闹钟"\
                                     "\n#3、删除已经创建的闹钟【已经激活的闹钟的无法关闭小睡闹钟】：\n删除闹钟+id【id先查询，空格有没有无所谓】"
                SendMsg.msg_sender(SendMsg, payload, param)
            #闹钟
            elif json["raw_message"][0:2] == "闹钟":
                message_info = json
                message_info['set_by'] = json['user_id']
                try:
                    alarm_id = AlarmBroadcast.alarm_command(json["raw_message"][2:], message_info)
                    if alarm_id == '格式错误':
                        payload["message"] = "格式错误"
                        SendMsg.msg_sender(SendMsg, payload, param)
                        return
                    payload["message"] = "已设置"
                    SendMsg.msg_sender(SendMsg, payload, param)
                    print(f'{json["user_id"]}创建了新闹钟')
                    return
                except:
                    payload["message"] = "格式错误"
                    SendMsg.msg_sender(SendMsg, payload, param)
                    return
            elif json["raw_message"] == "查询闹钟":
                msg = ''
                for alarm in AlarmBroadcast.Alarm.alarm['alarm_id']:
                    if AlarmBroadcast.Alarm.alarm[alarm]['set_by'] == json['user_id'] and AlarmBroadcast.Alarm.alarm[alarm]['repeat']['repeat_type'] != 'son':
                        msg += f'{AlarmBroadcast.Alarm.alarm[alarm]["alarm_name"]}:{alarm}' + '\n' + \
                               json_.dumps(AlarmBroadcast.Alarm.alarm[alarm], ensure_ascii = False, indent=4) + '\n'
                    if AlarmBroadcast.Alarm.alarm[alarm]['set_by'] in ['admin','Admin'] and \
                            json['user_id'] == Secure.admin:
                        msg += f'{AlarmBroadcast.Alarm.alarm[alarm]["alarm_name"]}:{alarm}' + '\n' + \
                               json_.dumps(AlarmBroadcast.Alarm.alarm[alarm], ensure_ascii=False, indent=4) + '\n'
                if msg == '':
                    payload["message"] = "无"
                    SendMsg.msg_sender(SendMsg, payload, param)
                    return
                payload['message'] = msg
                SendMsg.msg_sender(SendMsg, payload, param)
                return

            elif json["raw_message"][0:4] == "删除闹钟":
                for i in range(4, len(json["raw_message"])):
                    if i != '':
                        try:
                            if AlarmBroadcast.Alarm.alarm[json["raw_message"][i:]]['set_by'] == json['user_id']:
                                AlarmBroadcast.alarm_delete(json["raw_message"][i:])
                                payload["message"] = "已删除"
                                SendMsg.msg_sender(SendMsg, payload, param)
                            elif AlarmBroadcast.Alarm.alarm[json["raw_message"][i:]]['set_by'] in ['admin','Admin'] and json['user_id'] == Secure.admin:
                                AlarmBroadcast.alarm_delete(json["raw_message"][i:])
                                payload["message"] = "已删除"
                                SendMsg.msg_sender(SendMsg, payload, param)
                        except:
                            payload["message"] = "未查询到"
                            SendMsg.msg_sender(SendMsg, payload, param)
                        return
            '''
            #令牌重置
            elif json["raw_message"][0:4] == "重置令牌":
                Secure.get_secure_code(Secure, "new", json , None)
            #临时令牌
            elif json["raw_message"][0:4] == "临时令牌":
                for i in range(5, len(json["raw_message"])):
                    if not json["raw_message"][i].isdigit():
                        user_id = json["raw_message"][5:i+1]
                Secure.get_secure_code(Secure, "temp", json , user_id)
            #仪表盘
            '''

            return RecvHandler.log_sender(RecvHandler, "log_end")


        #群聊
        elif json["sub_type"] == "normal":
            payload["group_id"] = json["group_id"]#默认回复接收群组
            param = "/send_group_msg"
            #print(json)
            #判断是否at自己
            if json["raw_message"][0:21] == f"[CQ:at,qq={Secure.bot}]" or json["raw_message"][0:8] == '@Guluton':
                selecter = 0
                if json["raw_message"][0:21] == f"[CQ:at,qq={Secure.bot}]":
                    selecter = 21
                elif json["raw_message"][0:8] == '@Guluton':
                    selecter = 8
                #去除空格
                i = 0
                for i in range(selecter,len(json['raw_message'])):
                    if json['raw_message'][i] != " ":
                        break
                json['raw_message'] = json['raw_message'][0:selecter] + json['raw_message'][i:]
                RecvHandler.log_sender(RecvHandler, "log_head")
                print("at事件")
                #打招呼
                if json["raw_message"][selecter:] == "你好":
                    payload["message"] = "[CQ:at,qq=" + str(json["user_id"]) + "]你好吖"
                    SendMsg.msg_sender(SendMsg, payload , param)
                elif json["raw_message"][selecter:] in ["Hi","hi","嗨~","嗨","氦","hello",'Hello','哈喽']:
                    payload["message"] = "[CQ:at,qq=" + str(json["user_id"]) + "]Hi~"
                    SendMsg.msg_sender(SendMsg, payload , param)
                #字典相关
                elif json["raw_message"][selecter:] in ["字典列表"]:
                    payload["message"] = "[CQ:at,qq=" + str(json["user_id"]) + "]\n" + str(Dicts.lists)
                    SendMsg.msg_sender(SendMsg, payload , param)
                elif json["raw_message"][selecter:] in ["重载字典"]:
                    feedback = ""
                    if(json["user_id"] == Secure.admin):
                        Dicts.dict_searcher(Dicts, Config.dictposition)
                        feedback = "重载了：\n" + str(Dicts.lists)
                    else:
                        feedback = "你不是我的master，去联系他吧"
                    payload["message"] = "[CQ:at,qq=" + str(json["user_id"]) + "]" + feedback
                    SendMsg.msg_sender(SendMsg, payload , param)
                #帮助
                elif json["raw_message"][selecter:] in ["帮助",'help','Help','/h','/help','/Help','-h','--help']:
                    payload["message"] = "[CQ:at,qq=" + str(json["user_id"]) + "]\n" \
                                                                               "功能（需要at我）：网易云音乐，alarm，打招呼、帮助、" \
                                                                               "发送'字典列表'获取字典、发送'重载字典'重载字典文件（需要管理员操作）\n" \
                                                                               "不需要at我的：自动匹配聊天开头内容并回复固定内容\n" \
                                                                               "发送关键字播放《说的道理》\n" \
                                                                               "其余功能开发中。。。"
                    SendMsg.msg_sender(SendMsg, payload , param)
                elif json['raw_message'][selecter:] == '网易云音乐':
                    payload["message"] = "嗨，下面是网易云音乐相关用法（先@我然后）：\n#1、播放某用户的最近歌曲：\n" \
                                         "播放+（用户名）+的+（最近一周/所有时间）+（第/前）+（100以内阿拉伯数字）+首" \
                                         "\n#2、搜索歌曲：\n（搜索歌曲/搜索音乐）+（歌曲名）"\
                                         "\n#3、播放搜索结果内容\n播放+（歌曲名）+空格+（15以内数字，默认为1）"
                    SendMsg.msg_sender(SendMsg, payload, param)
                elif json['raw_message'][selecter:] == 'alarm':
                    #(1天/周后) 17:00(:30) 每周1,2,3/每2天 (小睡100,200,300) (名字：啦啦啦) (速速起床 某某图片)
                    payload["message"] = "先联系bot管理员添加该功能，中括号内为注释，括号内为非必选，括号不用加，注意区分中英文字符，空格，逗号等\n" \
                                         "嗨，下面是闹钟相关用法（先@我然后）：\n#1、设置一个闹钟：\n" \
                                         "闹钟+(1天/周后【不写默认当天】)空格17:30(:30【注意为英文冒号，秒不填默认为00】)空格" \
                                         "(每周1,2,3/每1天【注意为数字和英文逗号，不填默认只响一次】)" \
                                         "空格(小睡100,200,300【不填默认没有，十位数和个位数为秒数，百位数以上为分钟数，不能超过30分钟59秒】)空格" \
                                         "(名字：啦啦啦【注意为中文冒号，不加默认为”一个闹钟“】)空格(叫你时候发送的信息，用空格隔开)\n" \
                                         "注：时间后面的几个可选附加条件顺序不是固定的，建议把叫你时候发送的信息放在后面；空格要加，不管加几个反正要加" \
                                         "\n#2、发送你创建的闹钟以及相关信息：\n查询闹钟"\
                                         "\n#3、删除已经创建的闹钟【已经激活的闹钟的无法关闭小睡闹钟】：\n删除闹钟+id【id先查询，空格有没有无所谓】"
                    SendMsg.msg_sender(SendMsg, payload, param)

                #网易云音乐需要重构，先搁置
                elif json["raw_message"][selecter:selecter+2] == "播放":
                    print("##音乐事件")
                    RecvHandler.music_handler(RecvHandler,json["raw_message"][selecter:],payload,param)

                elif json["raw_message"][selecter:selecter+4] in ["搜索音乐",'搜索歌曲']:
                    print("##音乐事件")

                    #去除空格
                    i = selecter+4
                    for i in range(selecter+4,len(json["raw_message"])):
                        if json['raw_message'] != " ":
                            break
                    song_info = NeteaseMusicCrawler.get_search_songs(json["raw_message"][i:])
                    if song_info == "超时":
                        payload["message"] = "机器人连接超时(⊙﹏⊙)，请咨询管理"
                        SendMsg.msg_sender(SendMsg, payload, param)
                        return
                    if song_info == "无结果":
                        payload["message"] = "未找到你搜索的歌曲"
                        SendMsg.msg_sender(SendMsg, payload, param)
                        return
                    RecvHandler.music_search(RecvHandler,song_info,0,payload,param)

                #闹钟
                elif json["raw_message"][selecter:selecter + 2] == "闹钟" and json['group_id'] in Groups.group['alarm']:
                    message_info = json
                    message_info['set_by'] = json['user_id']
                    try:
                        alarm_id = AlarmBroadcast.alarm_command(json["raw_message"][selecter+2:], message_info)
                        if alarm_id == '格式错误':
                            payload["message"] = "格式错误"
                            SendMsg.msg_sender(SendMsg, payload, param)
                            return
                        payload["message"] = "已设置"
                        SendMsg.msg_sender(SendMsg, payload, param)
                        return
                        print(f'{json["user_id"]}创建了新闹钟')
                    except:
                        payload["message"] = "格式错误"
                        SendMsg.msg_sender(SendMsg, payload, param)
                    return

                elif json["raw_message"][selecter:] == "查询闹钟" and json['group_id'] in Groups.group['alarm']:
                    msg = ''
                    for alarm in AlarmBroadcast.Alarm.alarm['alarm_id']:
                        if AlarmBroadcast.Alarm.alarm[alarm]['set_by'] in ['admin','Admin'] and \
                                AlarmBroadcast.Alarm.alarm[alarm]['repeat']['repeat_type'] != 'son'\
                                and json['group_id'] in AlarmBroadcast.Alarm.alarm[alarm]['group_id']:
                            msg += f'{AlarmBroadcast.Alarm.alarm[alarm]["alarm_name"]}:{alarm}' + '\n' + \
                                   json_.dumps(AlarmBroadcast.Alarm.alarm[alarm], ensure_ascii = False, indent=4) + '\n'
                    if msg == '':
                        payload["message"] = "无"
                        SendMsg.msg_sender(SendMsg, payload, param)
                        return
                    new_content = {}
                    content = [{"type": "node", "data": {"name": "Guluton酱", "uin": str(Secure.bot),
                                                         "content": [{"type": "text", "data": {"text": msg}}]}}]
                    new_content['messages'] = content
                    new_content['group_id'] = json['group_id']
                    print('（发送了合并消息）')
                    SendMsg.msg_sender(SendMsg, new_content, '/send_group_forward_msg')
                    return

                elif json["raw_message"][selecter: selecter+4] == "删除闹钟" and json['group_id'] in Groups.group['alarm']:
                    for i in range(selecter+4, len(json["raw_message"])):
                        if i != '':
                            try:
                                if AlarmBroadcast.Alarm.alarm[json["raw_message"][i:]]['set_by'] == json['user_id']:
                                    AlarmBroadcast.alarm_delete(json["raw_message"][i:])
                                    payload["message"] = "已删除"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                elif AlarmBroadcast.Alarm.alarm[json["raw_message"][i:]]['set_by'] in ['admin','Admin'] and json[
                                    'user_id'] == Secure.admin:
                                    AlarmBroadcast.alarm_delete(json["raw_message"][i:])
                                    payload["message"] = "已删除"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                            except:
                                payload["message"] = "未查询到"
                                SendMsg.msg_sender(SendMsg, payload, param)
                            return

                #整个活
                elif json["raw_message"][selecter:] in ["整个活",'小亮给他整个活','草，走，忽略','整活']:
                    payload["message"] = '[CQ:image,file=zhenggehuo.gif]菊花喷火算吧？'
                    SendMsg.msg_sender(SendMsg, payload, param)
                #增删group组
                elif json["raw_message"][selecter:selecter+3] in ['add','del'] and json['user_id'] == Secure.admin:
                    for i in range(selecter+3, len(json['raw_message'])):
                        if json['raw_message'][i] != " ":
                            json['raw_message'] = json['raw_message'][0:selecter+3] + json['raw_message'][i:]
                            break
                    print(json['raw_message'])
                    if json["raw_message"][selecter:selecter+3] == 'add':
                        group_type = json["raw_message"][selecter+3:]
                        if not group_type in Groups.group['type_list']:
                            print('$$$$增删组事件：无更改')
                            payload["message"] = '无该类型'
                            SendMsg.msg_sender(SendMsg, payload, param)
                            return
                        if json['group_id'] in Groups.group[group_type]:
                            print('$$$$增删组事件：无更改')
                            payload["message"] = '已存在'
                            SendMsg.msg_sender(SendMsg, payload, param)
                            return
                        else:
                            Groups.group[group_type].append(json['group_id'])
                            IO.dict_writer(IO,Config.groupposition,Groups.group)
                            print(f'$$$$增删组事件：\n增加了{group_type}类型：群号{json["group_id"]}')
                            payload["message"] = '已增加'
                            SendMsg.msg_sender(SendMsg, payload, param)
                            return
                    if json["raw_message"][selecter:selecter+3] == 'del':
                        group_type = json["raw_message"][selecter+3:]
                        if not group_type in Groups.group['type_list']:
                            print('$$$$增删组事件：无更改')
                            payload["message"] = '无该类型'
                            SendMsg.msg_sender(SendMsg, payload, param)
                            return
                        if not json['group_id'] in Groups.group[group_type]:
                            print('$$$$增删组事件：无更改')
                            payload["message"] = '不存在'
                            SendMsg.msg_sender(SendMsg, payload, param)
                            return
                        else:
                            Groups.group[group_type].remove(json['group_id'])
                            IO.dict_writer(IO,Config.groupposition, Groups.group)
                            print(f'$$$$增删组事件：\n删除了{group_type}类型：群号{json["group_id"]}')
                            payload["message"] = '已删除'
                            SendMsg.msg_sender(SendMsg, payload, param)
                            return


                else:
                    payload["message"] = "[CQ:at,qq=" + str(json["user_id"]) + "]?"
                    SendMsg.msg_sender(SendMsg, payload, param)
                return RecvHandler.log_sender(RecvHandler, "log_end")

            #事件监视
            if json['group_id'] in Groups.group['render']:
                if json['raw_message'][0] == '【':
                    for selecter in range(0,len(json['raw_message'])):
                        if json['raw_message'][selecter] == '】':
                            result = MsgRender.handler(json['raw_message'][1:selecter])
                            result = copy.deepcopy(result)
                            if result['type'] == '全员核酸':
                                print(f'在{json["group_id"]}监测到全员核酸通知')
                                for i in range(0,len(result['content'][1])):
                                    #为每个闹钟加上日期
                                    result['content'][1][i]['alarm_time'][1] = result['content'][0][0]
                                    result['content'][1][i]['alarm_time'][2] = result['content'][0][1]
                                    #为每个闹钟加上群聊
                                    result['content'][1][i]['alarm_target']['group_id'] = Groups.group['全员核酸提醒']
                                    #创建闹钟
                                    new_id = AlarmBroadcast.get_id()
                                    AlarmBroadcast.alarm_create(result['content'][1][i],new_id)
                                return

            #说的道理
            if json["raw_message"][0:] in ["说的道理","啊米浴","阿米浴","说的道","阿米" , "啊米"]:
                RecvHandler.log_sender(RecvHandler, "log_head")
                payload["message"] = "正在向全体玩家高奏您的MVP凯歌:阿米浴说的道理\n" \
                                     "[CQ:image,file=shuodedaoli.gif]" \
                                     "\n大家好啊，我是：说的道理~！" \
                                     "\n今天来点大家想看的东西啊" \
                                     "\n啊！没出生在我心~" \
                                     "\n哈姆~一呼相当饿~" \
                                     "\n啊你，也列拿fish" \
                                     "\n黑波比麻fishes" \
                                     "\n啊米浴说的道理！" \
                                     "\n啊wish，多多wish！" \
                                     "\n啊饿~好饿一食得当" \
                                     "\n啊嘛啊！波比是我爹" \
                                     "\n啊~喵内地手啊呵呵木有" \
                                     "\nhttps://www.bilibili.com/video/BV1JB4y1s7Dk/" \
                                     "\n别急哦，将在60s后自动撤回"
                msg_id = SendMsg.msg_sender(SendMsg, payload, param)['data']['message_id']
                #print(SendMsg.msg_sender(SendMsg, payload, param))

                time_ = datetime.datetime.now() + datetime.timedelta(seconds = 60)
                Secure.set_delay_command(Secure,'delete',msg_id,AlarmBroadcast.datetime_to_list(time_))
                return RecvHandler.log_sender(RecvHandler, "log_end")
            #字典自动检测与翻译
            if json['group_id'] in Groups.group['dictplay']:
                for name in Dicts.lists:
                    if json["raw_message"] in Dicts.dictlist[name]:
                        if json["raw_message"] == '16****************head' or json["raw_message"] == '16****************end':
                            return
                        if type(Dicts.dictlist[name][json["raw_message"]]) == list:
                            print(Dicts.dictlist[name][json["raw_message"]][0])
                            payload["message"] = Dicts.dictlist[name]['16****************head'] + Dicts.dictlist[name][json["raw_message"]][0]
                            RecvHandler.log_sender(RecvHandler, "log_head")
                            SendMsg.msg_sender(SendMsg, payload, "/send_group_msg")
                            for son in range(1,len(Dicts.dictlist[name][json["raw_message"]])):
                                print(son)
                                payload["message"] = Dicts.dictlist[name][json["raw_message"]][son]
                                SendMsg.msg_sender(SendMsg, payload, "/send_group_msg")
                            if Dicts.dictlist[name]['16****************end'] != "":
                                payload["message"] = Dicts.dictlist[name]['16****************end']
                                SendMsg.msg_sender(SendMsg , payload , "/send_group_msg")
                            RecvHandler.log_sender(RecvHandler, "log_end")
                            return
                        elif type(Dicts.dictlist[name][json["raw_message"]]) == str:
                            print(Dicts.dictlist[name][json["raw_message"]])
                            payload["message"] = Dicts.dictlist[name]['16****************head'] + \
                                                 Dicts.dictlist[name][json["raw_message"]] + \
                                                 Dicts.dictlist[name]['16****************end']
                            RecvHandler.log_sender(RecvHandler, "log_head")
                            SendMsg.msg_sender(SendMsg, payload, "/send_group_msg")
                        return
            '''if '何同学' in json['raw_message']:
                payload['message'] = '⚠侦测到在途的何打击⚠\n⚠Heclear missile launch detected⚠\n' \
                                     '[CQ:image,file=994103f8038941ccc8261164aafb5005.image,subType=1,' \
                                     'url=https://gchat.qpic.cn/gchatpic_new/1103688627/583308472-3171020766-994103F8038941CCC8261164AAFB5005/0?term=3]' \
                                     '\n拦截失败，建议按何报复指导进行何报复'
                SendMsg.msg_sender(SendMsg, payload, "/send_group_msg")'''

        return

    def music_handler(self,msg,payload,param):
        # 现只有播放歌曲排行功能
        # 此为正则规则
        i = 0
        for i in range(2,len(msg)):
            if i != " ":
                break
        msg = msg[0:2] + msg[i:]
        if msg[-1] == "首":
            try:
                result = re.split(r'[播放 的 首]', msg)
                username = result[2]
                if username == '' or len(result) != 5:
                    print("格式错误")
                    payload["message"] = "格式有误呢，尝试：\n播放+（用户名）+的+（最近一周/所有时间）+（第/前）+（100以内阿拉伯数字）+首"
                    SendMsg.msg_sender(SendMsg, payload, param)
                    return
                mid = result[3]
                end = result[4]
                if end == '':
                    # print(mid)
                    for char in range(0, len(mid)):

                        if mid[char] == '前':
                            mid_result = re.split(r'前', mid)
                            if mid_result[0] in ['最近一周', '所有时间']:
                                type_ = mid_result[0]
                                try:
                                    number = int(mid_result[1])
                                except:
                                    print("格式错误")
                                    payload["message"] = "格式有误呢，尝试：\n播放+（用户名）+的+（最近一周/所有时间）+（第/前）+（100以内阿拉伯数字）+首"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return
                                if number > 100 or number < 1:
                                    print("格式错误")
                                    payload["message"] = "格式有误呢，尝试：\n播放+（用户名）+的+（最近一周/所有时间）+（第/前）+（100以内阿拉伯数字）+首"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return
                                print(username)
                                user_id = MC.get_userid(username)  # username, type_, number, '前'
                                if user_id == None:
                                    print("用户名错误")
                                    payload["message"] = "名字输入有误呢"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return
                                elif user_id == "超时":
                                    payload["message"] = "机器人连接超时(⊙﹏⊙)，请咨询管理"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return

                                song_info = MC.get_songs(user_id, type_, number, '前')

                                if song_info == "失败":
                                    payload["message"] = "您可能没开放听歌排行权限捏\n尝试到网易云音乐->设置->消息与隐私->我的听歌排行->所有人可见"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return
                                elif song_info == "超时":
                                    payload["message"] = "机器人连接超时(⊙﹏⊙)，请咨询管理"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return
                                elif song_info == "超出范围":
                                    payload["message"] = "貌似不在排行榜里"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return


                                RecvHandler.music_sender(RecvHandler, payload, param, song_info)
                                '''payload["message"] = str(song_info)
                                SendMsg.msg_sender(SendMsg, payload, param)
                                print(song_info)'''
                                return

                        elif mid[char] == '第':
                            mid_result = re.split(r'第', mid)
                            if mid_result[0] in ['最近一周', '所有时间']:
                                type_ = mid_result[0]
                                try:
                                    number = int(mid_result[1])
                                except:
                                    print("格式错误")
                                    payload["message"] = "格式有误呢，尝试：\n播放+（用户名）+的+（最近一周/所有时间）+（第/前）+（100以内阿拉伯数字）+首"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return
                                if number > 100 or number < 1:
                                    print("格式错误")
                                    payload["message"] = "格式有误呢，尝试：\n播放+（用户名）+的+（最近一周/所有时间）+（第/前）+（100以内阿拉伯数字）+首"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return
                                print(username)
                                user_id = MC.get_userid(username)#username, type_, number, '第'
                                if user_id == None:
                                    print("用户名错误")
                                    payload["message"] = "名字输入有误呢"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return
                                elif user_id == "超时":
                                    payload["message"] = "机器人连接超时(⊙﹏⊙)，请咨询管理"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return

                                song_info = MC.get_songs(user_id,type_,number,'第')

                                if song_info == "失败":
                                    payload["message"] = "您可能没开放听歌排行权限捏\n尝试到网易云音乐->设置->消息与隐私->我的听歌排行->所有人可见"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return
                                elif song_info == "超时":
                                    payload["message"] = "机器人连接超时(⊙﹏⊙)，请咨询管理"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return
                                elif song_info == "超出范围":
                                    payload["message"] = "貌似不在排行榜里"
                                    SendMsg.msg_sender(SendMsg, payload, param)
                                    return


                                RecvHandler.music_sender(RecvHandler, payload, param, song_info)
                                '''payload["message"] = str(song_info)
                                SendMsg.msg_sender(SendMsg, payload, param)
                                print(song_info)'''
                                return
            except:
                print("格式错误")
                payload["message"] = "格式有误呢，尝试：\n播放+（用户名）+的+（最近一周/所有时间）+（第/前）+（100以内阿拉伯数字）+首"
                SendMsg.msg_sender(SendMsg, payload, param)

        elif msg[-1].isdigit():
            try:
                rank = int(msg[-1])
                selecter = -1
                if msg[-2].isdigit():
                    rank = int(msg[-2:])
                    selecter = -2
                if (rank > 15 or rank < 1):
                    print('格式错误')
                    payload["message"] = "格式有误呢，尝试：\n播放+（歌曲名）+空格+（15以内数字，默认为1）"
                    SendMsg.msg_sender(SendMsg, payload, param)
                    return
                song_name = msg[2:selecter - 1]
                print(f'尝试播放{song_name}结果的第{rank}首')
                song_info = NeteaseMusicCrawler.get_search_songs(song_name)
                if song_info == "无结果":
                    payload["message"] = "未找到你搜索的歌曲，要不先尝试下搜索？"
                    SendMsg.msg_sender(SendMsg, payload, param)
                    return
                elif song_info == "超时":
                    payload["message"] = "机器人连接超时(⊙﹏⊙)，请咨询管理"
                    SendMsg.msg_sender(SendMsg, payload, param)
                    return
                return RecvHandler.music_search(RecvHandler, song_info, rank, payload, param)
            except:
                payload["message"] = "机器人连接超时(⊙﹏⊙)，请咨询管理"
                SendMsg.msg_sender(SendMsg, payload, param)
                return
        else:
            try:
                song_name = msg[2:]
                print(f'尝试播放{song_name}结果的第1首')
                song_info = NeteaseMusicCrawler.get_search_songs(song_name)
                if song_info == "无结果":
                    payload["message"] = "未找到你搜索的歌曲，要不先尝试下搜索？"
                    SendMsg.msg_sender(SendMsg, payload, param)
                    return
                elif song_info == "超时":
                    payload["message"] = "机器人连接超时(⊙﹏⊙)，请咨询管理"
                    SendMsg.msg_sender(SendMsg, payload, param)
                    return
                return RecvHandler.music_search(RecvHandler, song_info, 1, payload, param)
            except:
                payload["message"] = "机器人连接超时(⊙﹏⊙)，请咨询管理"
                SendMsg.msg_sender(SendMsg, payload, param)
                return
        payload["message"] = "Guluton酱没听懂你在说什么"
        SendMsg.msg_sender(SendMsg, payload, param)
        return

    def music_sender(self, payload, param, song_info):
        '''例子song_info = {'song_id_list':[],'song_id':{'song_name':'xxx','song_author':'xx'}}'''
        #先发一手发送中一类的话安抚一下用户
        first_payload = payload
        new_payload = payload
        first_payload["message"] = "已获取搜索结果，发送中~"
        SendMsg.msg_sender(SendMsg, first_payload, param)
        #先判断list长度
        if len(song_info['song_id_list']) == 1:
            new_payload['message'] = "[CQ:music,type=163,id=" + str(song_info['song_id_list'][0]) + "]"
            SendMsg.msg_sender(SendMsg, new_payload, param)
        elif len(song_info['song_id_list']) > 1:
            new_payload['message'] = "因为某些问题暂时只能发送合并链接捏"
            SendMsg.msg_sender(SendMsg, new_payload, param)
            full_data = []
            rank = 0
            for i in song_info['song_id_list']:
                rank += 1
                #合并转发音乐有问题，等待官方修复
                '''new_payload = {}
                new_payload['user_id'] = 
                new_payload['message'] = "[CQ:music,type=163,id=" + str(id_list[i]) + "]"
                msg_id = {}
                msg_id = SendMsg.msg_sender(SendMsg, new_payload, '/send_private_msg')
            '''
            #构建cq消息
                cq_data = {}
                cq_data['type'] = 'node'
                cq_data['data'] = {}
                cq_data['data']['name'] = str(rank)
                cq_data['data']['uin'] = Secure.bot
                cq_data['data']['content'] = []
                content = {}
                content['type'] = 'text'
                content['data'] = {'text':f'{rank}. {song_info[i]["song_author"]}:{song_info[i]["song_name"]}\nhttps://music.163.com/#/song?id={i}'}
                '''content['type'] = 'music'
                content['data'] = {}
                content['data']['type'] = '163'
                content['data']['id'] = str(i)'''
                cq_data['data']['content'].append(content)

                full_data.append(cq_data)

            new_payload['messages'] = full_data
            print('（发送了合并消息）')
            SendMsg.msg_sender(SendMsg, new_payload, '/send_group_forward_msg')
        return

        #再根据长度分别发送单个以及多个

    def music_search(self, song_info, rank, payload, param):
        '''例子song_info = {'song_id_list':[],'song_id':{'song_name':'xxx','song_author':'xx'}}'''
        new_payload = payload
        first_payload = payload
        if rank == 0:
            first_payload['message'] = '可以用播放 +（搜索时曲名）+（空格）+（搜索结果序号）直接发送歌曲'
            SendMsg.msg_sender(SendMsg, first_payload, param)
            msg = ''
            num = 0
            for id in song_info['song_id_list']:
                num += 1
                msg += str(num) + '.# 曲名：' + song_info[id]['song_name'] + '\n作者：' \
                        '' + song_info[id]['song_author'] + '\n链接：https://music.163.com/#/song?id=' + id
                if id != song_info['song_id_list'][-1]:
                    msg += '\n'
            content = [{"type": "node","data": {"name": "Guluton酱","uin": str(Secure.bot),"content": [{"type": "text","data": {"text":msg}}]}}]
            new_payload['messages'] = content
            print('（发送了合并消息）')
            SendMsg.msg_sender(SendMsg, new_payload, '/send_group_forward_msg')
            return
        else:
            new_payload['message'] = 'Guluton酱为你找到啦！'
            SendMsg.msg_sender(SendMsg, new_payload, param)
            new_rank = rank - 1
            id = song_info['song_id_list'][new_rank]
            msg = "[CQ:music,type=163,id=" + id + "]"
            new_payload['message'] = msg
            SendMsg.msg_sender(SendMsg, new_payload, param)
            return

    '''
    log_head日志头部
    log_end日志尾部
    其余直接打印
    '''
    def log_sender(self, content):
        if content == "log_head":
            print("\n", "-" * 20, "\n系统时间：", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), sep="")
        elif content == "log_end":
            print("-" * 20, sep="")
        else:
            print(content)
            return



class Secure:
    bot = 0
    admin = 0
    code = ""
    temp_code = ""
    temp_code_status = False
    temp_user = ""
    temp_time = ""
    temp_level = 0

    def set_delay_command(self,command_type,additionparam,time_):
        AlarmBroadcast.alarm_construct('Admin', command_type, time_, {} , [command_type,additionparam], [], {"repeat_type": "command"})

    def command(self,command_type,additionparam):
        if command_type in ['delete']:
            if command_type == 'delete':
                print(f'安全指令：撤回{additionparam}')
                SendMsg.msg_sender(SendMsg,{'message_id':additionparam},'/delete_msg')
        return

'''
    def secure_code_confirm(self, code):
        return

    #生成密钥
    def secure_code_generate(self, length):
        secure_code = ""
        basestr = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
        for i in range(0 , length):
            secure_code += basestr[random.randint(0 , len(basestr)-1)]
        return secure_code

    #获取密钥
    def get_secure_code(self, type, user, temp_user):
        if user["user_id"] == Secure.admin:
            if type == "temp":
                Secure.temp_code = Secure.secure_code_generate(Secure, 8)

            elif type == "new":
                payload = {}
                Secure.code = Secure.secure_code_generate(Secure, 32)
                payload["user_id"] = user["user_id"]
                payload["message"] = "主人保管好你的新令牌喔~\n" + str(Secure.code)
                RecvHandler.log_sender(RecvHandler, "##令牌已重置")
                return SendMsg.msg_sender(SendMsg, payload, "/send_private_msg")
        else:
            payload = {}
            RecvHandler.log_sender(RecvHandler, "##非管理用户尝试获取令牌")
            print(user)
            payload["user_id"] = user["user_id"]
            payload["message"] = "可是你好像不是我的主人吖"
            return SendMsg.msg_sender(SendMsg, payload, "/send_private_msg")
'''

class AlarmHandler:
    def check(self):
        #轮询闹钟
        for id in AlarmBroadcast.Alarm.alarm['alarm_id']:
            result = AlarmBroadcast.time_check(id)
            #过滤报错
            #print(result)
            if result != None:
                #执行管理命令
                if result['repeat']['repeat_type'] == 'command':
                    return Secure.command(Secure,result['alarm_message'][0],result['alarm_message'][1])

                #广播给群组
                for group_id in result['alarm_target']['group_id']:
                    payload = {}
                    payload['group_id'] = group_id
                    for msg in result["alarm_message"]:
                        payload['message'] = msg
                        SendMsg.msg_sender(SendMsg, payload, "/send_group_msg")
                for user_id in result['alarm_target']['user_id']:
                    payload = {}
                    payload['user_id'] = user_id
                    for msg in result["alarm_message"]:
                        payload['message'] = msg
                        SendMsg.msg_sender(SendMsg, payload, "/send_private_msg")
        return


def main():
    set_up()

    print('初始化完毕')
    while(1):
        AlarmHandler.check(AlarmHandler)
        msg = RecvMsg.msg_rec(RecvMsg)
        if msg != None:
            RecvHandler.main_handler(RecvHandler, msg)
        else:
            continue
    return

if __name__ == '__main__':
    main()
