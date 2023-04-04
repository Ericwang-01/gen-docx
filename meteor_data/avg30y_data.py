# -*- coding: utf-8 -*-
from __future__ import print_function
import pandas as pd
from datetime import datetime, timedelta
from ._base import MeteorBaseModel
from .evapotranspiration import BasicParameter
from .mmut_map import MMUT_MAP


def get_season_seq(dt):
    if not isinstance(dt, datetime):
        raise TypeError("Params Must Datetime Type")
    if dt.month in [3, 4, 5]:
        return "1"
    elif dt.month in [6, 7, 8]:
        return "2"
    elif dt.month in [9, 10, 11]:
        return "3"
    else:
        return "4"


class Avg30yDataModel(MeteorBaseModel):
    pre_tm_period = {2: 1, 3: 5, 4: 10, 5: 30, 6: 90, 7: 366}
    # Computing Tm Seq Mapper
    time_map = {
        2: lambda dt: str(dt.timetuple().tm_yday),
        3: lambda dt: "72" if dt.month == 12 and dt.day == 31 else str(int((dt.month - 1) * 6 + (int(dt.day / 5) + 1))),
        4: lambda dt: str(int(3 * (dt.month - 1) + (dt.day / 10) + 1)),
        5: lambda dt: str(dt.month),
        6: lambda dt: get_season_seq(dt),
        7: lambda dt: "19812010",
    }

    def __init__(self, fields, stations, period, db_connect):
        MeteorBaseModel.__init__(self)
        self.fields = fields
        self.stations = stations
        self.period = period
        self.db_connect = db_connect

    def fetch_data(self, tm):
        """
        获取累年值数据
        :param tm: 时间粒度 1-7 许
        :return:
        """
        st = datetime.strptime(self.period[0], "%Y-%m-%d")
        et = datetime.strptime(self.period[1], "%Y-%m-%d")
        print(st, et)
        # 历史数据查询 使用2000年可能导致与实际查询年份错位一天 故提前一天
        # 2021-11-19: 修复由起始日期提前一天引发的SEQ错误  改为生成SEQ LIST时直接添加前一天对应SEQ
        before_date = st - timedelta(days=1)
        seq_list = [self.time_map[tm](before_date)]
        for i in range(5000):
            if st > et:
                break
            if tm in range(2, 8):
                seq_list.append(self.time_map[tm](st))
                st = st + timedelta(days=self.pre_tm_period[tm])
            else:
                print("当前时间粒度无法获取累年值数据")
                exit(1)
        is_ssp = "ssp" in self.fields  # 此条件判断是否要根据ssh计算ssp
        print(is_ssp)
        if tm == 2:  # 累年日值表中没有ssp字段,故特殊处理
            self.fields = [i for i in self.fields if i != "ssp"]
        sql_fields = [MMUT_MAP[tm][x] for x in self.fields]
        sql = """
SELECT station_id_c as station, {4}, {0}
FROM {3} WHERE station_id_c IN ('{1}') AND {4} IN ('{2}')
ORDER BY station_id_c ASC ,{4} ASC
        """.format(", ".join(sql_fields), "','".join(self.stations), "','".join(seq_list), self.MMUT_TABLE_MAP[tm],
                   MMUT_MAP[tm]["date"])
        cursor = self.db_connect.cursor()
        cursor.execute(sql)
        labels = ["station"] + [MMUT_MAP[tm]["d"]] + list(self.fields)
        print(labels)
        rows = cursor.fetchall()
        df = pd.DataFrame([[self._row_f[i > 1](row[i]) for i in range(len(labels))] for row in rows], columns=labels)
        if tm == 2 and is_ssp:
            et = BasicParameter()
            # todo : 修改经纬度顺序 2022-04-24
            station_data = pd.read_csv("station.csv")
            station_lat_dict = {str(int(sta)): lat for sta, lat in zip(station_data['code'], station_data['lat'])}
            ssp_list = []
            for idx, row in df.iterrows():
                c_date = datetime(st.year, 1, 1).date() + timedelta(days=int(row["date"]))
                ssl = et.sun_rise_time(c_date, station_lat_dict[row["station"]])
                ssp_list.append(round(row["ssh"] / ssl[1] * 100, 2))
            df["ssp"] = ssp_list
        m = df > df
        for k in labels[2:]:
            m[k] = df[k] > 30000.0
        return df.mask(m)

    def fetch_data_origin(self):
        """
        信明原有的获取常年的函数
        :return:
        """
        sql_fields = ['r.%s' % x for x in self.fields]
        print(sql_fields)
        sql = """
SELECT l.station_id_c as station, to_char(l.datetime, 'YYYY-MM-DD') AS date, {0}
FROM meteo_surf_day_nm l JOIN meteo_surf_day_cn_avg_30y r
ON l.station_id_c = r.station_id_c AND (l.year - 11) / 10 = r.year / 10 AND l.month=r.month AND l.day=r.day
WHERE l.station_id_c IN ('{1}') AND l.datetime BETWEEN '{2}'
        """.format(", ".join(sql_fields), "','".join(self.stations), "' AND '".join(self.period))
        cursor = self.db_connect.cursor()
        cursor.execute(sql)
        labels = [str(row[0]) for row in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame([[self._row_f[i > 1](row[i]) for i in range(len(labels))] for row in rows], columns=labels)

        m = df > df
        for k in labels[2:]:
            m[k] = df[k] > 2000.0
        return df.mask(m)
