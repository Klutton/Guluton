import time
import json
import uuid
import datetime
import re
import copy

"""
感觉需要一个初始化的操作，读写应当由这个模块自行解决
对于循环闹钟，只更改其触发事件，对于snooze产生的闹钟，设置repeat_type为son
"""
class SetupPosition:
    alarmposition = ""
class Alarm:
    alarm = {}
class Weekday:
    day = {'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thu': 4, 'Fri': 5, 'Sat': 6, 'Sun': 7}
class Transform:
    target = {'normal':'group_id','friend':'user_id'}


#获取闹钟id
def get_id():
    get_timestamp_uuid = str(uuid.uuid1())
    return get_timestamp_uuid


#获取当前时间，返回类型为int
def get_time():
    return int(time.strftime("%Y%m%d%H%M%S"))


#接收并处理指令
def alarm_command(content,message_info):
    #先判断给谁开闹钟
    set_by = message_info['user_id']
    target = {'group_id':[],'user_id':[]}
    if type(message_info['sub_type']) == str:
        target[Transform.target[message_info['sub_type']]].append(message_info[Transform.target[message_info['sub_type']]])
    elif type(message_info['sub_type']) == list:
        for i in message_info['sub_type']:
            target[Transform.target[message_info['sub_type'][i]]].append(message_info[Transform.target[message_info['sub_type']]])
    else:
        return
    for i in range(0,len(content)):
        if content[i] != " ":
            content = content[i:]
            break
    #初始化闹钟
    alarm_name = '一个闹钟'
    message = []
    message.append(f'由{str(set_by)}设置的闹钟')
    repeat = {}
    repeat['repeat_type'] = 'no'
    snooze = []
    for i in range(0, len(content)):
        if content[i] != " ":
            content = content[i:]
            break
    # 再获取闹钟  |(1天/周后) 17:00(:30) 每周1,2,3/每2天 (小睡100,200,300) (名字：啦啦啦) (速速起床 某某图片)
    # 分离空格
    content_split = re.split(" ", content)
    # 分离多空格
    while ('' in content_split):
        content_split.remove('')
    # 开始分支结构
    delta_day = 0
    time_ = 0
    # 只输入时间默认为当天
    if len(content_split) == 1:
        # 分离冒号
        exact_time = re.split(":", content_split[0])
        time_ = int(exact_time[0]) * 10000 + int(exact_time[1]) * 100
        if len(exact_time) == 3:
            time_ += int(exact_time[2])
    # 输入了几天后以及时间
    elif len(content_split) > 1:
        # 分离冒号
        selecter = 0
        if content_split[0][-1] == '后':
            selecter += 1
        exact_time = re.split(":", content_split[selecter])
        time_ = int(exact_time[0]) * 10000 + int(exact_time[1]) * 100
        if len(exact_time) == 3:
            time_ += int(exact_time[2])
        if selecter == 1:
            if content_split[0][-2] == '天':
                delta_day = int(content_split[0][:-2])
            elif content_split[0][-2] == '周':
                delta_day = int(content_split[0][:-2]) * 7

        set_repeat = True
        set_snooze = True
        set_name = True
        for words in range(selecter + 1, len(content_split)):
            # 匹配关键词
            if content_split[words][0] == '每' and set_repeat:
                if content_split[words][1] == '周':
                    repeat['repeat_type'] = 'week'
                    repeat['day'] = []
                    # 分离得到每周几，去重
                    temp = list(set(re.split(",", content_split[words][2:])))
                    for splitday in range(0, len(temp)):
                        temp[splitday] = int(temp[splitday])
                    temp.sort()
                    if temp[0] < 1 or temp[-1] > 7:
                        print('格式错误')
                        return "格式错误"
                    for splitday in temp:
                        repeat['day'].append(splitday)
                else:
                    repeat['repeat_type'] = 'day'
                    stepday = int(content_split[words][1:-1])
                    if stepday < 1:
                        print('格式错误')
                        return "格式错误"
                    repeat['every'] = stepday
                set_repeat = False
            elif content_split[words][0:2] == '小睡' and set_snooze and content_split[words][2] in ['0', '1', '2', '3',
                                                                                                    '4', '5', '6', '7',
                                                                                                    '8', '9']:
                temp = list(set(re.split(",", content_split[words][2:])))
                for splitsnooze in range(0, len(temp)):
                    temp[splitsnooze] = int(temp[splitsnooze])
                temp.sort()
                for splitsnooze in temp:
                    if splitsnooze > 3000 or int(splitsnooze%100) > 59:
                        return '格式错误'
                    snooze.append(splitsnooze)
                set_snooze = False
            elif content_split[words][0:3] == '名字：' and set_name:
                set_name = False
                alarm_name = content_split[words][2:]
            else:
                message.append(content_split[words])

    time_ += int((datetime.datetime.now() + datetime.timedelta(days=delta_day)).strftime("%Y%m%d")) * 1000000
    if time_ < get_time():
        return '格式错误'
    #创建闹钟
    return alarm_construct(set_by,alarm_name,time_,target,message,snooze,repeat)


#检查目标id的闹钟是否到时间了
def time_check(id):
    #先判断是否存在该闹钟
    if not id in Alarm.alarm['alarm_id']:
        return "不存在"
    #再判断时间是否超出1min
    if get_time() > Alarm.alarm[id]['alarm_time'] + 100:
        alarm_delete(id)
        return "超时"
    #再判断时间是否在1min以内
    if get_time() in range(Alarm.alarm[id]['alarm_time'],Alarm.alarm[id]['alarm_time'] + 100):
        #判断是否有小睡
        if len(Alarm.alarm[id]['snooze']) != 0:
            #继承并创建新的同名闹钟
            for delay in Alarm.alarm[id]['snooze']:
                new_snooze_alarm = copy.deepcopy(Alarm.alarm[id])
                new_id = get_id()
                #为新闹钟附加新的id
                ##############################################################这里用的是现在的时间加延迟时间，为了避免丢失闹钟
                new_snooze_alarm['alarm_time'] = get_time() + delay
                #重命名小睡闹钟
                new_snooze_alarm['alarm_name'] += '(小睡闹钟)'
                #消息附加
                new_snooze_alarm['alarm_message'].append('（这是小睡闹钟）')
                #消除snooze
                new_snooze_alarm['snooze'] = []
                #更改闹钟类型
                new_snooze_alarm['repeat']['repeat_type'] = 'son'
                alarm_create(new_snooze_alarm,new_id)

        #判断是否有循环闹钟
        if not Alarm.alarm[id]['repeat']['repeat_type'] in ['no','son']:
            alarm_time = Alarm.alarm[id]['alarm_time']
            if Alarm.alarm['repeat']['repeat_type'] == 'week':
                #看今天是周几，匹配下一天,创建新闹钟
                today = Weekday.day[time.strftime('%a')]
                for i in range(0,len(Alarm.alarm['repeat']['day'])):
                    #如果长度为1，说明为每周循环，直接日期+7
                    if len(Alarm.alarm['repeat']['day']) == 1:
                        new_time = int((datetime.datetime.now()+datetime.timedelta(days=7)).strftime("%Y%m%d"))*1000000 + int(alarm_time%1000000)
                        new_alarm = {}
                        new_id = get_id()
                        new_alarm[new_id] = Alarm.alarm[id]
                        new_alarm[new_id]['alarm_time'] = new_time
                        alarm_create(new_alarm,new_id)
                        break
                    if Alarm.alarm['repeat']['day'][i] == today:
                        p = i+1
                        if p == len(Alarm.alarm['repeat']['day']):
                            p = 0
                        #下一天
                        nextday = Alarm.alarm['repeat']['day'][p]
                        if nextday < today:
                            nextday += 7
                        new_time = int((datetime.datetime.now() + datetime.timedelta(days=(nextday - today))).strftime("%Y%m%d")) * 1000000 + int(
                            alarm_time % 1000000)
                        new_alarm = {}
                        new_id = get_id()
                        new_alarm[new_id] = Alarm.alarm[id]
                        new_alarm[new_id]['alarm_time'] = new_time
                        alarm_create(new_alarm, new_id)
                        break

            if Alarm.alarm['repeat']['repeat_type'] == 'day':
                step = Alarm.alarm[id]['repeat']['every']
                new_time = int(
                    (datetime.datetime.now() + datetime.timedelta(days=step)).strftime("%Y%m%d")) * 1000000 + int(
                    alarm_time % 1000000)
                new_alarm = {}
                new_id = get_id()
                new_alarm[new_id] = Alarm.alarm[id]
                new_alarm[new_id]['alarm_time'] = new_time
                alarm_create(new_alarm, new_id)

        #获取闹钟内容
        alarm_result = Alarm.alarm[id]

        #删除已经响了的闹钟
        alarm_delete(id)
        print(f'闹钟响了{datetime.datetime.now()}')
        #返回闹钟json
        return alarm_result


#删除闹钟
def alarm_delete(id):
    Alarm.alarm['alarm_id'].remove(id)
    del Alarm.alarm[id]
    alarm_save()
    return


#构建一个闹钟
def alarm_construct(setby: str, name: str,time_: int,target: dict,message: list,snooze: list,repeat: dict):
    new_alarm = {}
    new_id = get_id()
    new_alarm['set_by'] = setby
    new_alarm['alarm_name'] = name
    new_alarm['alarm_time'] = time_
    new_alarm["alarm_target"] = target
    new_alarm["alarm_message"] = message
    new_alarm["snooze"] = snooze
    new_alarm["repeat"] = repeat
    alarm_create(new_alarm,new_id)
    return new_id


#创建新的闹钟，格式为一整个json
def alarm_create(json_,id):
    Alarm.alarm['alarm_id'].append(id)
    Alarm.alarm[id] = json_
    alarm_save()
    print(f'新建了闹钟，id：{id}')
    return


#将alarm信息存入json
def alarm_save():
    with open(SetupPosition.alarmposition,'w',encoding='utf-8') as fr:
        fr.write(json.dumps(Alarm.alarm))
    print('闹钟保存')
    return


#初始化
def alarm_setup(alarmposition):
    SetupPosition.alarmposition = alarmposition
    with open(SetupPosition.alarmposition, 'r', encoding='utf-8') as fr:
        Alarm.alarm = json.loads(fr.read())
    return