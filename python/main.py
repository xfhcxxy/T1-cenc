# -*- coding: utf-8 -*-
# @Time : 2022/6/23 14:50
# @Author : 向宇
# @File : main.py
import time

import requests
from mongoengine import Document, StringField, FloatField, DateTimeField, IntField, connect, disconnect
import time
import datetime
import ast

url = "http://www.ceic.ac.cn/ajax/search"

_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.3"
}

EPS = 1e-6          # 用于浮点数比较

M = []              # 震级
O_TIME = []         # 发震时刻(UTC+8)
EPI_LAT = []        # 纬度(°)
EPI_LON = []        # 经度(°)
EPI_DEPTH = []      # 深度(千米)
LOCATION_C = []     # 参考位置


def retrive(url, params):
    response = requests.get(url, headers=_header, params=params)
    text = response.content.decode()
    x = text.find('[')
    y = text.find(']')
    text = "," + text
    texts = text[x+1:y].split("}")
    for i in range(len(texts)):
        texts[i] = texts[i][1:]
        texts[i] += '}'
    return texts


error_tips = ["远海", "附近", "海域", "（有感）", "西岸", "东岸", "南岸", "北岸", "南部", "北部", "西部", "东部", "东北部",
              "东南部", "西北部", "西南部", "以东", "以南", "以北", "以西", "沿岸", "中部", "近海", "地区", "（塌陷）",
              "（矿震）", "（爆破）", "（更正）"]


def correct_location(loc):
    for tip in error_tips:
        if tip in loc:
            l = loc.index(tip)
            r = l + len(tip)
            loc = loc[:l] + loc[r:]
    return loc


def parse(texts, data_lastest):
    for text in texts:
        data_dict = ast.literal_eval(text)
        sub_keys = ['M', 'O_TIME', 'EPI_LAT', 'EPI_LON', 'EPI_DEPTH', 'LOCATION_C']
        data_dict = dict([(key, data_dict[key]) for key in sub_keys])
        data_dict['LOCATION_C'] = correct_location(data_dict['LOCATION_C'])
        print(data_dict)
        if data_dict['M'] == str(data_lastest.M) and data_dict['O_TIME'] == str(data_lastest.O_TIME) and float(data_dict['EPI_LAT']) - data_lastest.EPI_LAT < EPS and float(data_dict['EPI_LON']) - data_lastest.EPI_LON < EPS and data_dict['EPI_DEPTH'] == data_lastest.EPI_DEPTH and data_dict['LOCATION_C'] == str(data_lastest.LOCATION_C):
            print("该数据已在数据库中！停止爬虫！")
            return True
        EPI(**data_dict).save()
    return False


class EPI(Document):
    M = FloatField()
    O_TIME = DateTimeField()
    EPI_LAT = FloatField()
    EPI_LON = FloatField()
    EPI_DEPTH = IntField()
    LOCATION_C = StringField()


def main():
    try:
        num = len(EPI.objects().order_by('O_TIME'))
        data_lastest = EPI.objects().order_by('O_TIME')[num-1]
    except IndexError:
        data_lastest = EPI()
    for page in range(1, 517):
        print(f"第{page}页")
        params = {
            "start": "",
            "end": "",
            "jingdu1": "",
            "jingdu2": "",
            "weidu1": "",
            "weidu2": "",
            "height1": "",
            "height2": "",
            "zhenji1": "",
            "zhenji2": "",
        }
        times = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        time_array = time.strptime(times, "%Y-%m-%d %H:%M:%S")
        time_stamp = int(time.mktime(time_array))  # 转换时间戳
        time.sleep(5)
        params["callback"] = f"jQuery180031232585725055584_1607253668377&_={time_stamp}"
        params["page"] = page
        content = retrive(url, params)
        end = parse(content, data_lastest)
        if end:
            break


if __name__ == '__main__':
    connect(host="mongodb://localhost/cenc")
    main()
    disconnect()