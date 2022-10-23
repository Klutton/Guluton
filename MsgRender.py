import re
import datetime
import json

class Timetable:
    time_table = {}

#{ 'type':'', content:{}/[] }
def handler(msg):
    if len(msg) > 8:
        if msg[-6:] == '全员核酸检测':
            date = re.split('月', msg[0:-6])
            date[1] = date[1][0:-1]
            date[0] = int(date[0])
            date[1] = int(date[1])
            result = {'type': '全员核酸', 'content': [date,Timetable.time_table['全员核酸']]}
            return result


def time_table_edit(table_name):
    return


def set_up(timetableposition):
    with open(timetableposition,'r',encoding='GBK') as fr:
        Timetable.time_table = json.loads(fr.read())
    return