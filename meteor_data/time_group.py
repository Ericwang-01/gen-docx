# -*- coding: utf-8 -*-
import numpy as np


def date2ymd(dt, f):
    y, m, d = dt.split('-')
    return [y, m, str(f(int(d)))]


def f_pentad(x):
    xs = x.split("/")
    i5 = {"1": '初', "2": '二', "3": '三', "4": "四", "5": "五", "6": "末"}
    return "%s年%s月%s候" % (xs[0], xs[1], i5[xs[2]])


def f_i10days(x):
    xs = x.split("/")
    i10 = {"1": '上', "2": '中', "3": '下'}
    return "%s年%s月%s旬" % (xs[0], xs[1], i10[xs[2]])


def date2season(dt):
    y, m, d = dt.split('-')
    y, m = int(y), int(m)
    if m < 3:
        y -= 1
    if m in [3, 4, 5]:
        s = '春'
    elif m in [6, 7, 8]:
        s = '夏'
    elif m in [9, 10, 11]:
        s = '秋'
    else:
        s = '冬'
    return '%d年%s季' % (y, s)


def rg_period(tm, period):
    """
    Regroup Time Period
    @param tm: 
    @param period:
    @return: 
    """
    if 2 < tm < 5:
        return [period[0][0], period[1][1]]
    elif tm == 5:  # 月的时间格外处理
        last_day_map = {1: "-31", 2: "-28", 3: "-31", 5: "-31", 7: "-31", 9: "-31", 10: "-31", 12: "-31", }
        if int(period[1][-2:]) in last_day_map.keys():
            last_day = last_day_map[int(period[1][-2:])]
        else:
            last_day = "-30"
        return [period[0] + "-01", period[1] + last_day]
    elif tm == 6:  # 季的时间格外处理
        return [period[0][0], period[1][1]]
    elif tm == 7:  # 年的时间格外处理
        return [period[0] + "-01-01", period[1] + "-12-31"]
    else:
        return period


class TimeGroup(object):
    group = {
        1: {"label": "时", "key": "hour", "func": lambda x: x},
        2: {"label": "日", "key": "date", "func": lambda x: x},
        3: {
            "label": "候", "key": "pentad",
            "func": lambda x: "/".join(date2ymd(x, lambda d: int((d + 4) / 5) - int(d / 31)))
        },
        4: {
            "label": "旬", "key": "i10days",
            "func": lambda x: "/".join(date2ymd(x, lambda d: int((d + 9) / 10) - int(d / 31)))
        },
        5: {"label": "月", "key": "month", "func": lambda x: x[:7]},
        6: {"label": "季", "key": "season", "func": date2season},
        7: {"label": "年", "key": "year", "func": lambda x: x[:4]},
    }

    func = {"avg": np.mean, "mean": np.mean, "sum": np.sum, "max": np.max, "min": np.min}

    def __init__(self):
        pass

    @staticmethod
    def get_season_seq_by(season_chn_name):
        if season_chn_name == "春季":
            return 1
        elif season_chn_name == "夏季":
            return 2
        elif season_chn_name == "秋季":
            return 3
        else:
            return 4
