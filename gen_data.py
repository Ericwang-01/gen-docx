# -*- coding:utf-8 -*-
import json
import psycopg2
import pandas as pd
from meteor_data.error import gen_http_status
from meteor_data.daily_data import DailyDataModel
from meteor_data.evapotranspiration import BasicParameter

# STATION_CSV = "station.csv"
# STATION_JSON = "script/parameter/station_code.json"
# TRANSLATE_JSON = "script/parameter/field_translate.json"
# DSN = 'host=127.0.0.1 port=5433 dbname=nmnq_db user=nmnq password=nmnq'

STATION_CSV = "/data1/CR/json_file/station.csv"
STATION_JSON = "/data1/CR/json_file/parameter/station_code.json"
TRANSLATE_JSON = "/data1/CR/json_file/parameter/field_translate.json"
DSN = 'host=192.168.3.218 dbname=nmnq_db user=nmnq password=nmnq'


# 获取基本数据
def get_m_data(stations, period):
    fields = ('year', 'month', 'day', 'tem_avg', 'tem_max', 'tem_min', 'rhu_avg', 'ssh', 'pre_time_2020', 'win_s_max')
    db_connect = psycopg2.connect(DSN)

    # 获取基本数据
    meteor_obj = DailyDataModel(fields, stations, period, db_connect)
    m_data = meteor_obj.fetch_data()
    if len(m_data) < 1:
        gen_http_status({"status": 400, "msg": "当前时间段无数据"})
    m_data['win_s_max'] = m_data['win_s_max'] > 17.1  # 根据最大风速判断风级是否大于7级

    # 站点经纬度信息
    station_data = pd.read_csv(STATION_CSV)
    # 站点和纬度组装字典
    if isinstance(station_data.iloc[0, 0], str):
        station_lat_dict = {str(sta): lat for sta, lat in zip(station_data['code'], station_data['lat'])}
    else:
        station_lat_dict = {str(int(sta)): lat for sta, lat in zip(station_data['code'], station_data['lat'])}

    # 计算日照百分率
    et = BasicParameter()
    ssp_list = []
    for _, row in m_data.iterrows():
        ssl = et.sun_rise_time(row["date"], station_lat_dict[row["station"]])
        ssp_list.append(round(row["ssh"] / ssl[1] * 100, 2))
    m_data["ssp"] = ssp_list

    # 插入站点名
    station_map = json.loads(open(STATION_JSON, encoding="utf-8").read())
    station_name = [station_map[i] for i in m_data["station"]]
    m_data.insert(1, "station_name", station_name)
    m_data.dropna(inplace=True)

    return m_data


# task_param调用
def run():
    with open('task_param.json', 'r') as f:
        argv = json.loads(f.read())

    # 读取参数
    stations = argv.get('stations')  # 站点号列表
    time = argv.get('time')  # 时间参数
    period = time.get('period')  # 时间区间
    term = time.get('groupby')  # 周期：旬、月

    # 按粒度调整period时间样式
    if term == 4:
        period = [period[0][0], period[1][1]]
    elif term == 5:
        last_day_map = {1: "-31", 2: "-28", 3: "-31", 5: "-31", 7: "-31", 8: "-31", 10: "-31", 12: "-31", }
        if int(period[1][-2:]) in last_day_map.keys():
            last_day = last_day_map[int(period[1][-2:])]
        else:
            last_day = "-30"
        period = [period[0] + "-01", period[1] + last_day]

    # 获取气象数据
    m_data = get_m_data(stations, period)
    translate_map = json.loads(open(TRANSLATE_JSON, encoding='utf-8').read())
    re_columns = {i: translate_map[i] for i in m_data.columns}
    m_data.rename(columns=re_columns, inplace=True)
    m_data.to_csv('result.csv', float_format='%.1f', index=False, encoding='utf_8_sig')

    with open('report_info.json', 'w') as f:
        f.write(json.dumps(m_data.to_dict(orient='records',), ensure_ascii=False))


if __name__ == '__main__':
    run()
