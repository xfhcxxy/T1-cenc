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
from pyecharts.charts import Timeline
from pyecharts import options as opts
from pyecharts.globals import ThemeType

path = os.path.dirname(os.path.realpath(sys.executable))
#path = os.path.abspath('.')
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
??????????????????
'''
def draw_pot_all_pot(lat, lon):  # ???????????????
    lat = np.array(lat)
    lon = np.array(lon)
    world_map = folium.Map(location=[35.3, 100.6], zoom_start=4, control_scale=True, )
    incidents = folium.map.FeatureGroup()
    for i in range(len(lat)):
        incidents.add_child(
            folium.CircleMarker(  # ??????
                (lat[i], lon[i]),  # ????????????????????????
                radius=3,  # ????????????
                color='#FF1493',  # ?????????????????????
                fill=True,  # ????????????
                fill_color='#00FF00',  # ????????????
                fill_opacity=0.4  # ???????????????
            )
        )
    world_map.add_child(incidents)
    world_map.save(os.path.join(save_path, 'pot_all_pot.html'))


''' 
????????????????????????????????????????????????????????????????????????????????????
'''
def draw_pot_market_pot(lat, lon):  # ???????????????
    lat = np.array(lat)
    lon = np.array(lon)
    world_map = folium.Map(location=[35.3, 100.6], zoom_start=4, control_scale=True, )
    marker_cluster = plugins.MarkerCluster().add_to(world_map)
    for i in range(len(lat)):
        folium.Marker(location=[lat[i], lon[i]]).add_to(marker_cluster)
    world_map.save(os.path.join(save_path, 'pot_market_pot.html'))


'''
???????????????
'''
def draw_heat_map_static(m, lat, lon):
    data = []
    for i in range(len(m)):
        data.append([lat[i], lon[i], m[i]/10])
    world_map = folium.Map(location=[35.3, 100.6], zoom_start=4, control_scale=True, )
    HeatMap(data, radius=20).add_to(world_map)
    world_map.save(os.path.join(save_path, 'heat_map_static.html'))


'''
???????????????
t = y ????????????
t = m ????????????????????????
t = d ????????????
'''
def draw_heat_map_dynamic(m, date, lat, lon, t='m'):
    data = []  # ?????????
    data_m = []  # ???????????????????????????
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
????????? ??????-??????
'''
def draw_line_m_to_num(m):
    line = Line(init_opts=opts.InitOpts(width="1200px", height="700px", theme=ThemeType.DARK, bg_color="rgb(21, 28, 57)"))
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
    line.add_yaxis("????????????", y, is_clip=True,
                   symbol='circle',
                   symbol_size=8,
                   linestyle_opts=opts.LineStyleOpts(width=3, color="rgb(63, 177, 227)"),
                   itemstyle_opts=opts.ItemStyleOpts(color="rgb(63, 177, 227)")
                   )
    line.set_series_opts(
        areastyle_opts=opts.AreaStyleOpts(opacity=0.5, color="rgb(50, 132, 176)"),
        label_opts=opts.LabelOpts(is_show=False),
    )
    line.set_global_opts(
        title_opts=opts.TitleOpts(title="??????????????????????????????", subtitle="????????????", pos_left='center', pos_top='top'),
        legend_opts=opts.LegendOpts(is_show=False)
    )
    line.render(os.path.join(save_path, 'line_m_to_num.html'))


'''
??????-?????????????????????
t = y ????????????
t = m ????????????????????????
t = d ????????????
'''
def draw_line_time_to_num(date, t='m'):
    line = Line(init_opts=opts.InitOpts(width="1200px", height="700px", theme=ThemeType.DARK, bg_color="rgb(21, 28, 57)"))
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
    line.add_yaxis("????????????", y, is_clip=True,
                   symbol='circle',
                   symbol_size=8,
                   linestyle_opts=opts.LineStyleOpts(width=3, color="rgb(63, 177, 227)"),
                   itemstyle_opts=opts.ItemStyleOpts(color="rgb(63, 177, 227)")
                   )
    line.set_series_opts(
        areastyle_opts=opts.AreaStyleOpts(opacity=0.5, color="rgb(50, 132, 176)"),
        label_opts=opts.LabelOpts(is_show=False),
    )
    line.set_global_opts(
        title_opts=opts.TitleOpts(title="??????????????????????????????", subtitle="????????????", pos_left='center', pos_top='top'),
        legend_opts=opts.LegendOpts(is_show=False),
    )
    line.render(os.path.join(save_path, 'line_time_to_num.html'))


'''
?????????????????????????????????
'''
def draw_word_cloud(loc):
    cloud = WordCloud(
        init_opts=opts.InitOpts(width="1200px", height="700px", bg_color="rgb(21, 28, 57)", theme=ThemeType.DARK),

    )
    count = {}
    for l in loc:
        if l not in count:
            count[l] = 0
        count[l] += 1
    loc = list(set(loc))
    data = []
    for l in loc:
        data.append((l, count[l]))
    cloud.add(
        series_name="??????",
        data_pair=data,
        shape="circle"
    )
    cloud.render(os.path.join(save_path, 'word_cloud.html'))


'''
?????? ???????????????????????????- ??????
'''
def draw_pie_m_to_num(m):
    pie = Pie(init_opts=opts.InitOpts(width="1200px", height="700px", theme=ThemeType.DARK, bg_color="rgb(21, 28, 57)"))
    count = {}
    for i in range(len(m)):
        m[i] = str(int(float(m[i])))+"?????????"
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
    pie.set_global_opts(title_opts=opts.TitleOpts(title="?????? ???????????????????????????- ??????"))
    pie.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
    pie.render(os.path.join(save_path, 'pie_m_to_num.html'))


'''
??????????????? ??????
'''
def draw_rank_list_dynamic(date, loc):
    for i in range(len(date)):
        date[i] = date[i][:4]
    time_line = Timeline(init_opts=opts.InitOpts(width="440px", height="300px", theme=ThemeType.DARK, bg_color="rgb(21, 28, 57)"))
    count = {}
    num = len(date)
    for i in range(num):
        if loc[i] not in count:
            count[loc[i]] = 0
        count[loc[i]] += 1
        if i == num-1 or date[i] != date[i+1]:
            count = sorted(count.items(), key=lambda x: x[1], reverse=True)
            x = []
            y = []
            for item in count[:10]:
                x.append(item[0])
                y.append(item[1])
            x.reverse()
            y.reverse()
            bar = (
                Bar(init_opts=opts.InitOpts(width="440px", height="380px", theme=ThemeType.DARK, bg_color="rgb(21, 28, 57)"))
                .add_xaxis(x)
                .add_yaxis("???????????????", y)
                .reversal_axis()
                .set_global_opts(title_opts=opts.TitleOpts(title='??????????????????', subtitle="????????????", pos_left='center', pos_top='top'),
                                 legend_opts=opts.LegendOpts(is_show=False),
                                 visualmap_opts=opts.VisualMapOpts(
                                     is_show=False, pos_top='center', range_color=['lightskyblue', 'yellow', 'orangered'], min_=0, max_=9)
                                 )
                .set_series_opts(label_opts=opts.LabelOpts(is_show=True, position='right', color='white'))

            )
            time_line.add(bar, date[i]).add_schema(is_auto_play=True)
            count = {}
    time_line.render(os.path.join(save_path, 'rank_list_dynamic.html'))


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
    print("????????????", file=f)
    draw_pot_all_pot(lat, lon)
    print("???????????????", file=f)
    draw_pot_market_pot(lat, lon)
    print("????????????????????????", file=f)
    draw_heat_map_static(m, lat, lon)
    print("????????????????????????", file=f)
    draw_heat_map_dynamic(m, date, lat, lon, t='m')
    print("????????????????????????", file=f)
    draw_line_time_to_num(date, t='m')
    print("?????????????????????????????????????????????", file=f)
    draw_line_m_to_num(m)
    print("?????????????????????????????????????????????", file=f)
    draw_word_cloud(loc)
    print("?????????????????????", file=f)
    draw_pie_m_to_num(m)
    print("?????????????????????", file=f)
    draw_rank_list_dynamic(date, loc)
    print("??????????????????", file=f)
    disconnect()
    f.close()
