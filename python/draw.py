import sys
import numpy as np
import datetime
import time
import os

from mongoengine import Document, StringField, FloatField, DateTimeField, IntField, connect, disconnect
from mongoengine.queryset.visitor import Q
import folium
from folium import plugins
from folium.plugins import HeatMap
from pyecharts.charts import Bar
from pyecharts.charts import Line
from pyecharts.charts import WordCloud
from pyecharts.charts import Pie
from pyecharts.faker import Faker
from pyecharts import options as opts
from pyecharts.globals import ThemeType

# path = os.path.dirname(os.path.realpath(sys.executable))
path = os.path.abspath('.')
save_path = os.path.join(path, 'map')
log_path = os.path.join(path, 'log')
f = open(os.path.join(log_path, 'draw.txt'), 'w')

date_start = datetime.datetime.strptime("2000-01-01 01:01:01", "%Y-%m-%d %H:%M:%S")
date_end = datetime.datetime.strptime("2200-01-01 01:01:01", "%Y-%m-%d %H:%M:%S")


class EPI(Document):
    M = FloatField()
    O_TIME = DateTimeField()
    EPI_LAT = FloatField()
    EPI_LON = FloatField()
    EPI_DEPTH = IntField()
    LOCATION_C = StringField()


def read_data(m_1=0.0, m_2=10.0, time_1="2000-01-01", time_2="2200-01-01", lat_1=-90.0, lat_2=90.0, lon_1=-180.0,
              lon_2=180.0, dep_1=0, dep_2=100):
    time_1 += " 00:00:01"
    time_2 += " 23:59:59"
    time_1 = datetime.datetime.strptime(time_1, "%Y-%m-%d %H:%M:%S")
    time_2 = datetime.datetime.strptime(time_2, "%Y-%m-%d %H:%M:%S")
    datas = EPI.objects(Q(M__gte=m_1) & Q(M__lte=m_2) & Q(O_TIME__gte=time_1) & Q(O_TIME__lte=time_2) &
                        Q(EPI_LAT__gte=lat_1) & Q(EPI_LAT__lte=lat_2) & Q(EPI_LON__gte=lon_1) & Q(EPI_LON__lte=lon_2) &
                        Q(EPI_DEPTH__gte=dep_1) & Q(EPI_DEPTH__lte=dep_2)).order_by('O_TIME')
    num = len(datas)
    m = []
    date_time = []
    lat = []
    lon = []
    dep = []
    loc = []
    for data in datas:
        m.append(float(data.M))
        date_time.append(data.O_TIME)
        lat.append(float(data.EPI_LAT))
        lon.append(float(data.EPI_LON))
        dep.append(int(data.EPI_DEPTH))
        loc.append(str(data.LOCATION_C))
    return m, date_time, lat, lon, dep, loc


'''
同时画所有点
'''


def draw_pot_all_pot(lat, lon):  # 纬度和经度
    lat = np.array(lat)
    lon = np.array(lon)
    world_map = folium.Map(location=[35.3, 100.6], zoom_start=4, control_scale=True, )
    incidents = folium.map.FeatureGroup()
    for i in range(len(lat)):
        incidents.add_child(
            folium.CircleMarker(  # 画圈
                (lat[i], lon[i]),  # 地震源经纬度坐标
                radius=3,  # 圆圈半径
                color='#FF1493',  # 标志的外圈颜色
                fill=True,  # 是否填充
                fill_color='#00FF00',  # 填充颜色
                fill_opacity=0.4  # 填充透明度
            )
        )
    world_map.add_child(incidents)
    world_map.save(os.path.join(save_path, 'pot_all_pot.html'))


''' 
一个区域类的点会合成一个点，点上数字表示这个区域有多少点
'''


def draw_pot_market_pot(lat, lon):  # 纬度和经度
    lat = np.array(lat)
    lon = np.array(lon)
    world_map = folium.Map(location=[35.3, 100.6], zoom_start=4, control_scale=True, )
    marker_cluster = plugins.MarkerCluster().add_to(world_map)
    for i in range(len(lat)):
        folium.Marker(location=[lat[i], lon[i]]).add_to(marker_cluster)
    world_map.save(os.path.join(save_path, 'pot_market_pot.html'))


'''
静态热力图
'''


def draw_heat_map_static(m, lat, lon):
    data = []
    for i in range(len(m)):
        data.append([lat[i], lon[i], m[i]])
    world_map = folium.Map(location=[35.3, 100.6], zoom_start=4, control_scale=True, )
    HeatMap(data).add_to(world_map)
    world_map.save(os.path.join(save_path, 'heat_map_static.html'))


'''
动态热力图
t = y 按年划分
t = m 按月划分（默认）
t = d 按日划分
'''


def draw_heat_map_dynamic(m, date, lat, lon, t='m'):
    data = []  # 总数据
    data_m = []  # 一个时间划分的数据
    date_m = []
    lim = 7
    if t == 'd':
        lim = 10
    elif t == 'y':
        lim = 4
    for i in range(len(m)):
        data_m.append([lat[i], lon[i], m[i]])
        if date[i][:lim] != date[i - 1][:lim]:
            data.append(data_m)
            data_m = []
            date_m.append(date[i][:lim])

    world_map = folium.Map(location=[35.3, 100.6], zoom_start=4, control_scale=True, )
    plugins.HeatMapWithTime(data, index=date_m).add_to(world_map)
    world_map.save(os.path.join(save_path, 'heat_map_dynamic.html'))


'''
折线图 震级-次数
'''


def draw_line_m_to_num(m):
    line = Line(init_opts=opts.InitOpts(width="1200px", height="700px", theme=ThemeType.DARK))
    count = {}
    for i in range(len(m)):
        m[i] = str(m[i])
    for i in m:
        if i not in count:
            count[i] = 0
        count[i] += 1
    m = list(set(m))
    m.sort()
    line.add_xaxis(m)
    y = []
    for x in m:
        y.append(count[x])
    line.add_yaxis("地震次数", y, is_clip=True)
    line.render(os.path.join(save_path, 'line_m_to_num.html'))


'''
时间-地震次数折线图
t = y 按年划分
t = m 按月划分（默认）
t = d 按日划分
'''


def draw_line_time_to_num(date, t='m'):
    line = Line(init_opts=opts.InitOpts(width="1200px", height="700px", theme=ThemeType.DARK))
    lim = 7
    if t == 'd':
        lim = 10
    elif t == 'y':
        lim = 4
    for i in range(len(date)):
        date[i] = date[i][:lim]
    date_dict = {}
    for d in date:
        if d not in date_dict:
            date_dict[d] = 0
        date_dict[d] += 1
    date = list(set(date))
    date.sort()
    line.add_xaxis(date)
    y = []
    for d in date:
        y.append(date_dict[d])
    line.add_yaxis("地震次数", y, is_clip=True)
    line.render(os.path.join(save_path, 'line_time_to_num.html'))


'''
词云，体现地点地震频率
'''
def draw_word_cloud(loc):
    cloud = WordCloud(init_opts=opts.InitOpts(width="1200px", height="700px", theme=ThemeType.DARK))
    count = {}
    for l in loc:
        if l not in count:
            count[l] = 0
        count[l] += 1
    loc = list(set(loc))
    data = []
    for l in loc:
        data.append((l, count[l]))
    cloud.add(series_name="震源", data_pair=data, shape="circle")
    cloud.render(os.path.join(save_path, 'word_cloud.html'))


'''
饼图 震级（精确到个位）- 次数
'''
def draw_pie_m_to_num(m):
    pie = Pie(init_opts=opts.InitOpts(width="1200px", height="700px", theme=ThemeType.DARK))
    count = {}
    for i in range(len(m)):
        m[i] = str(int(m[i]))+"级地震"
    for i in m:
        if i not in count:
            count[i] = 0
        count[i] += 1
    m = list(set(m))
    m.sort()
    y = []
    for x in m:
        y.append(count[x])
    pie.add("", [list(z) for z in zip(m, y)])
    pie.set_global_opts(title_opts=opts.TitleOpts(title="饼图 震级（精确到个位）- 次数"))
    pie.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
    pie.render(os.path.join(save_path, 'pie_m_to_num.html'))


if __name__ == '__main__':
    connect(host="mongodb://localhost/cenc")
    m1 = 0.0
    m2 = 10.0
    time1 = "2000-01-01"
    time2 = "2222-01-01"
    lat1 = -90.0
    lat2 = 90.0
    lon1 = -180.0
    lon2 = 180.0
    dep1 = 0
    dep2 = 100
    print(time.time(), file=f)
    if len(sys.argv) > 1:
        argv = sys.argv[1]
        argv = argv.split('&')
        num_argv = len(argv)
        print(argv, file=f)
        try:
            if num_argv >= 2 and len(argv[1]) > 1:
                m1 = float(argv[1][1:])
        except ValueError:
            pass
        try:
            if num_argv >= 3 and len(argv[2]) > 1:
                m2 = float(argv[2][1:])
        except ValueError:
            pass
        try:
            if num_argv >= 4 and len(argv[3]) > 1:
                time1 = str(argv[3][1:])
        except ValueError:
            pass
        try:
            if num_argv >= 5 and len(argv[4]) > 1:
                time2 = str(argv[4][1:])
        except ValueError:
            pass
        try:
            if num_argv >= 6 and len(argv[5]) > 1:
                lat1 = float(argv[5][1:])
        except ValueError:
            pass
        try:
            if num_argv >= 7 and len(argv[6]) > 1:
                lat2 = float(argv[6][1:])
        except ValueError:
            pass
        try:
            if num_argv >= 8 and len(argv[7]) > 1:
                lon1 = float(argv[7][1:])
        except ValueError:
            pass
        try:
            if num_argv >= 9 and len(argv[8]) > 1:
                lon2 = float(argv[8][1:])
        except ValueError:
            pass
        try:
            if num_argv >= 10 and len(argv[9]) > 1:
                dep1 = int(argv[9][1:])
        except ValueError:
            pass
        try:
            if num_argv >= 11 and len(argv[10:-1]) > 1:
                dep2 = int(argv[10][1:-1])
        except ValueError:
            pass

    m, date_time, lat, lon, dep, loc = read_data(m_1=m1, m_2=m2, time_1=time1, time_2=time2, lat_1=lat1, lat_2=lat2,
                                                 lon_1=lon1, lon_2=lon2, dep_1=dep1, dep_2=dep2)
    date = []
    time = []
    for dt in date_time:
        date.append(str(dt).split(' ')[0])
        time.append(str(dt).split(' ')[1])
    '''
    print("开始绘图", file=f)
    draw_pot_all_pot(lat, lon)
    print("绘制完点图", file=f)
    draw_pot_market_pot(lat, lon)
    print("绘制完带标记点图", file=f)
    draw_heat_map_static(m, lat, lon)
    print("绘制完静态热力图", file=f)
    draw_heat_map_dynamic(m, date, lat, lon, t='m')
    print("绘制完动态热力图", file=f)
    draw_line_time_to_num(date, t='m')
    print("绘制完时间与地震次数关系折线图", file=f)
    draw_line_m_to_num(m)
    print("绘制完震级与地震次数关系折线图", file=f)
    draw_word_cloud(loc)
    print("绘制完地点云图", file=f)
    '''
    draw_pie_m_to_num(m)
    print("绘制完震级饼图", file=f)
    disconnect()
    f.close()
