# -*- coding: utf-8 -*-
import decimal
import numpy as np
import pandas as pd


class MeteorBaseModel(object):
    # 处理db结果类型为Decimal的问题
    _row_f = {True: lambda x: MeteorBaseModel.row_f_t(x), False: lambda x: x}

    MMUT_TABLE_MAP = {
        2: "surf_chn_day_mmut",
        3: "surf_chn_pen_mmut",
        4: "surf_chn_ten_mmut",
        5: "surf_chn_mon_mmut",
        6: "surf_chn_season_mmut",
        7: "surf_chn_yer_mmut"
    }

    agg_default = {
        "tem_avg": np.mean,
        "tem_avg_mmut": np.mean,
        "tem_avg_anomaly": np.mean,
        "tem_max": np.max,
        "tem_min": np.min,
        "pre": np.sum,
        "pre_time_2008": np.sum,
        "pre_time_0820": np.sum,
        "pre_time_2020": np.sum,
        "pre_time_2020_mmut": np.sum,
        "pre_time_2020_r_anomaly": np.mean,
        "pre_time_0808": np.sum,
        "prs_avg": np.mean,
        "prs_max": np.max,
        "prs_min": np.min,
        "gst_avg": np.mean,
        "gst_max": np.max,
        "gst_min": np.min,
        "gst_avg_5cm": np.mean,
        "gst_avg_10cm": np.mean,
        "gst_avg_15cm": np.mean,
        "gst_avg_20cm": np.mean,
        "gst_avg_40cm": np.mean,
        "rhu_avg": np.mean,
        "rhu_min": np.min,
        "win_s": np.mean,
        "win_s_max": np.max,
        "win_s_inst_max": np.max,
        "win_s_2mi_avg": np.mean,
        "win_s_10mi_avg": np.mean,
        "frs_1st_top": np.mean,
        "v20330_01": np.mean,
        "frs_1st_bot": np.mean,
        "v20331_01": np.mean,
        "frs_2nd_top": np.mean,
        "v20330_02": np.mean,
        "frs_2nd_bot": np.mean,
        "v20331_02": np.mean,
        "snow_depth": np.mean,
        "v13013": np.mean,
        "snow_prs": np.mean,
        "v13330": np.mean,
        "ssh": np.sum,
        "ssl": np.sum,
        "ssp": np.mean,
        "vap_avg": np.mean,
        "evp": np.sum,
        "evp_big": np.sum,
        "hargreaves": np.sum,
        "priestley_taylor": np.sum,
        "penman_monteith": np.sum
    }

    def __init__(self):
        self.fields = []

    @classmethod
    def clean_data(cls, data, fields, period_particle_size="daily", agg_default=None):
        pps_func = {
            "daily": cls._pps_daily_data,
            "pentad": cls._pps_pentad_data,
            "i5days": cls._pps_pentad_data,
            "weekly": cls._pps_weekly_data,
            "i10days": cls._pps_i10days_data,
            "month": cls._pps_month_data,
            "season": cls._pps_season_data,
            "year": cls._pps_year_data
        }

        agg = {fk: cls.agg_default[fk] for fk in fields}
        if agg_default is not None:
            for fk in agg_default:
                agg[fk] = agg_default[fk]

        return pps_func[period_particle_size](data, agg)

    @classmethod
    def statistic_count_if(cls, mask, data, groupby_field):
        gpd = mask.groupby(groupby_field)
        return gpd.agg(np.sum).apply(cls.seq2str)

    @staticmethod
    def seq2str(x):
        if x is None:
            return ""
        try:
            return str(int(x))
        except ValueError:
            return ''

    @staticmethod
    def row_f_t(x):
        if x is None:
            return x
        try:
            # 998XXX: GE XXX Values
            if isinstance(x, decimal.Decimal) and 998000 <= x <= 998999:
                return float(str(x)[-5:])
            return float(x)
        except ValueError:
            return x

    @staticmethod
    def _pps_daily_data(data, agg):
        """
        日粒度输出
        :param data:
        :param agg:
        :return:
        """
        return data.groupby(["station", "date"]).agg(agg)

    @staticmethod
    def _pps_pentad_data(data, agg):
        """
        候粒度输出
        :param data:
        :param agg:
        :return:
        """
        data["pentad"] = data["date"].apply(
            lambda x: '%s-%s-%d' % (x[:4], x[5:7], int((int(x[-2:]) + 4) / 5) - int(int(x[-2:]) / 31))
        )
        return data.groupby(["station", "pentad"]).agg(agg)

    @staticmethod
    def _pps_weekly_data(data, agg):
        """
        周粒度输出（待修正）
        :param data:
        :param agg:
        :return:
        """
        data["week"] = data["date"].apply(lambda x: '%s-%s-%d' % (x[:4], x[5:7], int((int(x[-2:]) + 6) / 7)))
        return data.groupby(["station", "week"]).agg(agg)

    @staticmethod
    def _pps_i10days_data(data, agg):
        """
        旬粒度输出
        :param data:
        :param agg:
        :return:
        """
        data["i10days"] = data["date"].apply(
            lambda x: '%s-%s-%d' % (x[:4], x[5:7], int((int(x[-2:]) + 9) / 10) - int(int(x[-2:]) / 31))
        )
        return data.groupby(["station", "i10days"]).agg(agg)

    @staticmethod
    def _pps_month_data(data, agg):
        """
        月粒度输出
        :param data:
        :param agg:
        :return:
        """
        data["year-month"] = data["date"].apply(lambda x: '%s-%s' % (x[:4], x[5:7]))
        return data.groupby(["station", "year-month"]).agg(agg)

    @staticmethod
    def _pps_season_data(data, agg):
        """
        季粒度输出，春天从3月开始，冬季至次年2月止
        :param data:
        :param agg:
        :return:
        """
        data["season"] = data["date"].apply(
            # 下面变换待修正
            lambda x: '%s-%s-%d' % (x[:4], x[5:7], int((int(x[-2:]) + 4) / 5) - int(int(x[-2]) / 31))
        )
        return data.groupby(["station", "season"]).agg(agg)

    @staticmethod
    def _pps_year_data(data, agg):
        """
        年粒度输出
        :param data:
        :param agg:
        :return:
        """
        data["year"] = data["date"].apply(lambda x: x[:4])
        return data.groupby(["station", "year"]).agg(agg)

    @staticmethod
    def statistic_sum_if(mask, data, groupby_field):
        gpd = (mask * data).groupby(groupby_field)
        return gpd.agg(np.sum)

    @staticmethod
    def statistic_cond_max_numbs(mask, data, groupby_field):
        """
        满足条件最长统计
        """
        result = {}
        for sta, gx in mask.groupby(groupby_field):
            cm = []
            cc = 0
            for gix in gx:
                if not gix:
                    if cc not in cm:
                        cm.append(cc)
                    cc = 0
                else:
                    cc += 1
            cm.append(cc)
            result[sta] = max(cm)
        res_v = pd.DataFrame(result.values(), index=result.keys())
        res_v.index.name = tuple(groupby_field) if len(groupby_field) > 1 else groupby_field[0]
        return res_v

    @staticmethod
    def statistic_cond_max_value(df, data, groupby_field):
        """
        满足条件最大连续统计
        """
        result = {}
        if len(groupby_field) > 1:
            md = pd.concat([df, data], axis=1)
        else:
            md = pd.merge(df, data, on=df.index.names, how='left')
        for sta, gx in md.groupby(groupby_field):
            cm = []
            cb = None  # 原值0 可能会在负值max中产生错误 故修改
            cc = False
            for idx, gix in gx.iterrows():
                af, bf = gix
                if af:
                    if cc:
                        cm.append(max([bf, cb]))
                    else:
                        cb = bf
                        cc = True
                else:
                    cb = None
                    cc = False
            if len(cm) > 0:
                result[sta] = max(cm)
            else:
                result[sta] = None

        res_v = pd.DataFrame(result.values(), index=result.keys())
        res_v.index.name = tuple(groupby_field) if len(groupby_field) > 1 else groupby_field[0]
        return res_v
