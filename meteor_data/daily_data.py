# -*- coding: utf-8 -*-
import datetime
import pandas as pd
from ._base import MeteorBaseModel
from .time_group import TimeGroup


class DailyDataModel(MeteorBaseModel):
    def __init__(self, fields, stations, period, db_connect):
        MeteorBaseModel.__init__(self)
        self.fields = fields
        self.stations = stations
        self.period = period
        self.db_connect = db_connect

    def fetch_data(self):
        sql = """
SELECT station_id_c as station, to_char(datetime, 'YYYY-MM-DD') AS date, {0}
FROM meteo_surf_day_nm WHERE station_id_c IN ('{1}') AND datetime BETWEEN '{2}' ORDER BY station_id_c, datetime
""".format(",".join(self.fields), "','".join(self.stations), "' AND '".join(self.period))
        cursor = self.db_connect.cursor()
        cursor.execute(sql)
        labels = [str(row[0]) for row in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame([[self._row_f[i > 1](row[i]) for i in range(len(labels))] for row in rows], columns=labels)

        m = df > df
        m['date'] = False
        for k in labels[2:]:
            m[k] = df[k] > 999000.0
        return df.mask(m)

    def fetch_hour_data(self):
        self.period = [datetime.datetime.strptime(i, "%Y-%m-%d-%H").strftime("%Y-%m-%d %H:%M:%S") for i in self.period]
        field_list = []
        # 小时值降水只有一个值故特殊处理
        for i in self.fields:
            if i in ["pre_time_2020", "pre_time_0808", "pre_time_2008", "pre_time_0820"]:
                field_list.append("pre")
            elif i in ["prs_avg", "prs_max", "prs_min"]:
                field_list.append("prs")
            else:
                field_list.append(i)
        sql = """
SELECT station_id_c as station, to_char(datetime, 'YYYY-MM-DD-HH24') AS date, {0}
FROM meteo_surf_hour_cn WHERE station_id_c IN ('{1}') AND datetime BETWEEN '{2}' ORDER BY station_id_c, datetime
""".format(",".join(list(set(field_list))), "','".join(self.stations), "' AND '".join(self.period))
        cursor = self.db_connect.cursor()
        cursor.execute(sql)
        labels = [str(row[0]) for row in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame([[self._row_f[i > 1](row[i]) for i in range(len(labels))] for row in rows], columns=labels)

        m = df > df
        m['date'] = False
        for k in labels[2:]:
            m[k] = df[k] > 999000.0
        return df.mask(m)

    def fetch_diff_year_data(self, year_list, tm):
        if tm == 6:
            next_year_list = [i + 1 for i in year_list]
            # extend 会产生继承传递
            # year_list.extend(next_year_list)
            year_list = year_list + next_year_list
            year_list = [str(i) for i in set(year_list)]
        else:
            year_list = [str(i) for i in year_list]
        sql = """
SELECT r.station_id_c as station, to_char(r.datetime, 'YYYY-MM-DD') AS date, {0}
FROM meteo_surf_day_nm l JOIN meteo_surf_day_nm r
ON l.station_id_c=r.station_id_c AND l.month=r.month AND l.day=r.day
AND r.year in ('{2}') WHERE l.station_id_c IN ('{1}') AND l.datetime BETWEEN '{3}' ORDER BY r.station_id_c, r.datetime
""".format(
            ",".join(['r.%s AS %s' % (f, f) for f in self.fields]),
            "','".join(self.stations),
            "','".join(year_list),
            "' AND '".join(self.period)
        )
        print(sql)
        cursor = self.db_connect.cursor()
        cursor.execute(sql)
        labels = [str(row[0]) for row in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame([[self._row_f[i > 1](row[i]) for i in range(len(labels))] for row in rows], columns=labels)

        m = df > df
        m['date'] = False
        for k in labels[2:]:
            m[k] = df[k] > 999000.0
        return df.mask(m)

    def clean_data_anomaly(self, data, fields=None, period_particle_size="daily"):
        """
        计算距平
        :param data:
        :param fields:
        :param period_particle_size:
        :return:
        """
        from .avg30y_data import Avg30yDataModel
        if fields is None:
            fields = self.fields
        model = Avg30yDataModel(fields, self.stations, self.period, self.db_connect)
        data_30y = model.fetch_data()
        data_30y = model.clean_data(data_30y, fields, period_particle_size)
        for fk in fields:
            data["%s_anomaly" % fk] = data[fk] - data_30y[fk]
        return data

    def fetch_lxy_data(self, fields, ly=1, period_particle_size=2):
        """
        获取近X年历史数据
        :param fields, set of data fields
        :param ly, last years about history data
        :param period_particle_size
        :return DataFrame
        """
        sql = """
SELECT l.station_id_c as station, to_char(l.datetime, 'YYYY-MM-DD') AS date, {0}
FROM meteo_surf_day_nm l JOIN meteo_surf_day_nm r
ON l.station_id_c=r.station_id_c AND l.month=r.month AND l.day=r.day AND l.year-{1}<=r.year AND l.year>r.year
WHERE l.station_id_c IN ('{2}') AND l.datetime BETWEEN '{3}'
        """.format(
            ",".join(['r.%s AS %s' % (f, f) for f in fields]),
            ly,
            "','".join(self.stations),
            "' AND '".join(self.period)
        )
        cursor = self.db_connect.cursor()
        cursor.execute(sql)
        labels = [str(row[0]) for row in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame([[self._row_f[i > 1](row[i]) for i in range(len(labels))] for row in rows], columns=labels)

        m = df > df
        m['date'] = False
        for k in labels[2:]:
            m[k] = df[k] > 999000.0
        df = df.mask(m)
        m_tm = TimeGroup.group[period_particle_size]
        df[m_tm["key"]] = df['date'].apply(m_tm["func"])
        return df.groupby(['station', m_tm["key"]]).agg({k: self.agg_default[k] for k in fields})

    def fetch_lxy_data_user(self, fields, st, et, period_particle_size=2):
        """
        获取自定义历史数据
        :param st: 自定义起始年
        :param et: 自定义截止年
        :param fields, set of data fields
        :param period_particle_size
        :return DataFrame
        """
        sql = """
SELECT l.station_id_c as station, to_char(l.datetime, 'YYYY-MM-DD') AS date, {0}
FROM meteo_surf_day_nm l JOIN meteo_surf_day_nm r
ON l.station_id_c=r.station_id_c AND l.month=r.month AND l.day=r.day
AND {1}<=r.year AND {2}>=r.year WHERE l.station_id_c IN ('{3}') 
AND l.datetime BETWEEN '{4}'""".format(
            ",".join(['r.%s AS %s' % (f, f) for f in fields]),
            st,
            et,
            "','".join(self.stations),
            "' AND '".join(self.period)
        )
        cursor = self.db_connect.cursor()
        cursor.execute(sql)
        labels = [str(row[0]) for row in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame([[self._row_f[i > 1](row[i]) for i in range(len(labels))] for row in rows], columns=labels)

        m = df > df
        m['date'] = False
        for k in labels[2:]:
            m[k] = df[k] > 999000.0
        df = df.mask(m)
        m_tm = TimeGroup.group[period_particle_size]
        df[m_tm["key"]] = df['date'].apply(m_tm["func"])
        return df.groupby(['station', m_tm["key"]]).agg({k: self.agg_default[k] for k in fields})

    def fetch_hist_data(self, fields):
        sql_fields = ['r.%s' % x for x in fields]
        sql = """
SELECT l.station_id_c AS station, to_char(l.datetime, 'YYYY-MM-DD') AS date, r.year AS r_year, {0}
FROM meteo_surf_day_nm l LEFT JOIN meteo_surf_day_nm r
ON l.station_id_c=r.station_id_c AND l.month=r.month AND l.day=r.day AND l.year >= r.year
WHERE l.station_id_c IN ('{1}') AND l.datetime BETWEEN '{2}'
        """.format(', '.join(sql_fields), "','".join(self.stations), "' AND '".join(self.period))
        cursor = self.db_connect.cursor()
        cursor.execute(sql)
        labels = [str(row[0]) for row in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame([[self._row_f[i > 1](row[i]) for i in range(len(labels))] for row in rows], columns=labels)
        m = df > df
        m['date'] = False
        for k in labels[2:]:
            m[k] = df[k] > 999000.0
        return df.mask(m)

    def fetch_hist_data_hour(self, fields):
        sql_fields = ['r.%s' % x for x in fields]
        sql = """
SELECT l.station_id_c AS station, to_char(l.datetime, 'YYYY-MM-DD') AS date, r.year AS r_year, {0}
FROM meteo_surf_hour_cn l LEFT JOIN meteo_surf_hour_cn r
ON l.station_id_c=r.station_id_c AND l.month=r.month AND l.day=r.day AND l.hour=r.hour AND l.year >= r.year
WHERE l.station_id_c IN ('{1}') AND l.datetime BETWEEN '{2}'
        """.format(', '.join(sql_fields), "','".join(self.stations), "' AND '".join(self.period))
        print(sql)
        cursor = self.db_connect.cursor()
        cursor.execute(sql)
        labels = [str(row[0]) for row in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame([[self._row_f[i > 1](row[i]) for i in range(len(labels))] for row in rows], columns=labels)
        m = df > df
        m['date'] = False
        for k in labels[2:]:
            m[k] = df[k] > 999000.0
        return df.mask(m)

    def fetch_product_data(self):
        sql = """
SELECT l.station_id_c, l.datetime, r.day_seq , l.tem_avg, r.tem_avg AS tem_avg_mmut, 
l.tem_avg - r.tem_avg AS tem_avg_anomaly, l.tem_max, l.tem_min, l.pre_time_2020, r.pre_time_2020_mmut, 
(l.pre_time_2020 - r.pre_time_2020_mmut) AS pre_time_2020_anomaly, l.ssh, l.win_s_inst_max
FROM meteo_surf_day_nm l LEFT JOIN surf_chn_day_mmut r 
ON extract(DOY FROM l.datetime)=r.day_seq AND l.station_id_c = r.station_id_c
WHERE l.datetime BETWEEN '{1}' AND l.station_id_c IN ('{0}')
ORDER BY l.station_id_c, l.datetime""".format("','".join(self.stations), "' AND '".join(self.period))
        cursor = self.db_connect.cursor()
        cursor.execute(sql)
        labels = [str(row[0]) for row in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame([[self._row_f[i > 1](row[i]) for i in range(len(labels))] for row in rows],
                          columns=labels)

        m = df > df
        m['date'] = False
        for k in labels[2:]:
            m[k] = df[k] > 999000.0
        return df.mask(m)

    def get_last_wefc(self):
        sql = """SELECT station_id_c,validtime,tem_max_24h,tem_min_24h,wep FROM sevp_wefc
WHERE station_id_c IN ('{0}') AND datetime='{1}' AND validtime IN (24,48,72)""".format("','".join(self.stations),
                                                                                       self.period[-1])
        cursor = self.db_connect.cursor()
        cursor.execute(sql)
        labels = [str(row[0]) for row in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame([[self._row_f[i > 1](row[i]) for i in range(len(labels))] for row in rows],
                          columns=labels)

        m = df > df
        m['date'] = False
        for k in labels[2:]:
            m[k] = df[k] > 999000.0
        return df.mask(m)
