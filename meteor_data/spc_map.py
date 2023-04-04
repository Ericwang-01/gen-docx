# -*- coding: utf-8 -*-
from interval import Interval

__all__ = ["SPC_MAP"]

# x1为棚内前一日气温平均实测值；
# x2为棚外日最高气温预报值；
# x3为棚外日最低气温预报值；
# x4为棚外日照时数预报值；
# x5为棚外日总云量预报值（晴天取值0.0-1.9的平均值、晴间多云与多云天取值2.0-8.0的平均值、阴天取值8.1-10.0的平均值）。
# 索引0 棚内最高气温 索引1 棚内最低气温 索引2 棚内平均气温
SPC_MAP = {
    90501: {
        Interval(3, 999, lower_closed=True, upper_closed=True): "无霜冻",
        Interval(0, 3, lower_closed=True, upper_closed=False): "轻霜冻",
        Interval(-2.5, 0, lower_closed=True, upper_closed=False): "中霜冻",
        Interval(-999, -2.5, lower_closed=True, upper_closed=False): "重霜冻",
    },
    90502: {
        Interval(0, 999, lower_closed=True, upper_closed=True): "无霜冻",
        Interval(-1, 0, lower_closed=True, upper_closed=False): "轻霜冻",
        Interval(-2, -1, lower_closed=True, upper_closed=False): "中霜冻",
        Interval(-999, -2, lower_closed=True, upper_closed=False): "重霜冻",
    },
    90503: {
        Interval(2, 999, lower_closed=True, upper_closed=True): "无霜冻",
        Interval(0, 2, lower_closed=True, upper_closed=False): "轻霜冻",
        Interval(-2, 0, lower_closed=True, upper_closed=False): "中霜冻",
        Interval(-999, -2, lower_closed=True, upper_closed=False): "重霜冻",
    },
    90504: {
        Interval(-1, 999, lower_closed=True, upper_closed=True): "无霜冻",
        Interval(-2, -1, lower_closed=True, upper_closed=False): "轻霜冻",
        Interval(-3, -2, lower_closed=True, upper_closed=False): "中霜冻",
        Interval(-999, -3, lower_closed=True, upper_closed=False): "重霜冻",
    },
    90505: {
        Interval(0, 999, lower_closed=True, upper_closed=True): "无霜冻",
        Interval(-1, 0, lower_closed=True, upper_closed=False): "轻霜冻",
        Interval(-2, -1, lower_closed=True, upper_closed=False): "中霜冻",
        Interval(-999, -2, lower_closed=True, upper_closed=False): "重霜冻",
    },
    90506: {
        Interval(0.5, 999, lower_closed=True, upper_closed=True): "无霜冻",
        Interval(0, 0.5, lower_closed=True, upper_closed=False): "轻霜冻",
        Interval(-1, 0, lower_closed=True, upper_closed=False): "中霜冻",
        Interval(-999, -1, lower_closed=True, upper_closed=False): "重霜冻",
    },
    90507: {
        Interval(-1, 999, lower_closed=True, upper_closed=True): "无霜冻",
        Interval(-2, -1, lower_closed=True, upper_closed=False): "轻霜冻",
        Interval(-3, -2, lower_closed=True, upper_closed=False): "中霜冻",
        Interval(-999, -3, lower_closed=True, upper_closed=False): "重霜冻",
    },
    90508: {
        Interval(-0.5, 999, lower_closed=True, upper_closed=True): "无霜冻",
        Interval(-1, -0.5, lower_closed=True, upper_closed=False): "轻霜冻",
        Interval(-2, -1, lower_closed=True, upper_closed=False): "中霜冻",
        Interval(-999, -2, lower_closed=True, upper_closed=False): "重霜冻",
    },
    90509: {
        Interval(0.5, 999, lower_closed=True, upper_closed=True): "无霜冻",
        Interval(0, 0.5, lower_closed=True, upper_closed=False): "轻霜冻",
        Interval(-1, 0, lower_closed=True, upper_closed=False): "中霜冻",
        Interval(-999, -1, lower_closed=True, upper_closed=False): "重霜冻",
    },
    90510: {
        Interval(-999, 35, lower_closed=True, upper_closed=False): "无",
        Interval(35, 37, lower_closed=True, upper_closed=False): "轻",
        Interval(37, 39, lower_closed=True, upper_closed=False): "中",
        Interval(39, 999, lower_closed=True, upper_closed=True): "重",
    },
    90511: {
        Interval(-999, 17.2, lower_closed=True, upper_closed=False): "无",
        Interval(17.2, 24.5, lower_closed=True, upper_closed=False): "轻",
        Interval(24.5, 32.7, lower_closed=True, upper_closed=False): "中",
        Interval(32.7, 999, lower_closed=True, upper_closed=True): "重",
    },
    130101: {
        "tq_tem_max": lambda x1, x2, x3, x4, x5: 29.654 + 0.191 * x1 - 0.217 * x2 + 0.035 * x3 - 1.385 * x4,
        "tq_tem_min": lambda x1, x2, x3, x4, x5: 11.414 + 0.261 * x2 - 0.311 * x4 - 0.052 * x5,
        "tq_tem_avg": lambda x1, x2, x3, x4, x5: 17.054 + 0.116 * x1 + 0.252 * x3 - 0.404 * x4
    },
    130102: {
        "tq_tem_max": lambda x1, x2, x3, x4, x5: 28.732 + 0.174 * x1 + 0.167 * x2 + 0.011 * x3 + 1.422 * x4,
        "tq_tem_min": lambda x1, x2, x3, x4, x5: 10.398 + 0.280 * x2 - 0.196 * x4 - 0.01 * x5,
        "tq_tem_avg": lambda x1, x2, x3, x4, x5: 13.571 + 0.216 * x1 + 0.132 * x3 - 0.387 * x4
    },
    130103: {
        "tq_tem_max": lambda x1, x2, x3, x4, x5: 26.347 - 0.044 * x1 + 0.338 * x2 + 1.046 * x3 - 0.329 * x4,
        "tq_tem_min": lambda x1, x2, x3, x4, x5: 10.897 + 0.369 * x2 - 0.168 * x4 - 0.036 * x5,
        "tq_tem_avg": lambda x1, x2, x3, x4, x5: 10.524 + 0.341 * x1 + 0.347 * x3 - 0.056 * x4
    },
    130104: {
        "tq_tem_max": lambda x1, x2, x3, x4, x5: 24.968 + 0.097 * x1 + 0.321 * x2 + 0.829 * x3 - 0.092 * x4,
        "tq_tem_min": lambda x1, x2, x3, x4, x5: 11.434 + 0.403 * x2 - 0.09 * x4 - 0.09 * x5,
        "tq_tem_avg": lambda x1, x2, x3, x4, x5: 11.379 + 0.366 * x1 + 0.202 * x3 + 0.072 * x4
    },
    130105: {
        "tq_tem_max": lambda x1, x2, x3, x4, x5: 17.795 + 0.446 * x1 - 0.04 * x2 + 1.12 * x3 - 0.53 * x4,
        "tq_tem_min": lambda x1, x2, x3, x4, x5: 6.39 + 0.166 * x2 - 0.161 * x4 + 0.231 * x5,
        "tq_tem_avg": lambda x1, x2, x3, x4, x5: 8.384 + 0.437 * x1 + 0.446 * x3 - 0.272 * x4
    },
    130106: {
        "tq_tem_max": lambda x1, x2, x3, x4, x5: 5.189 + 0.628 * x1 - 0.633 * x2 + 0.974 * x3 + 0.338 * x4,
        "tq_tem_min": lambda x1, x2, x3, x4, x5: 4.383 + 0.532 * x2 - 0.02 * x4 + 0.197 * x5,
        "tq_tem_avg": lambda x1, x2, x3, x4, x5: -1.84 + 0.801 * x1 + 0.255 * x3 + 0.399 * x4
    },
    130201: {
        1: [
            lambda x1, x2, x3, x4, x5: 97.312 - 1.2 * x1 - 0.14 * x2 + 0.546 * x3 + 1.456 * x5,
            lambda x: x + 16,
            lambda x: x - 30
        ],
        2: [
            lambda x1, x2, x3, x4, x5: 55.408 - 0.109 * x2 + 1.312 * x4 + 3.414 * x5,
            lambda x: x + 19,
            lambda x: x - 21
        ],
        3: [
            lambda x1, x2, x3, x4, x5: 79.163 + 1.392 * x1 - 0.926 * x2 + 0.397 * x3 - 1.117 * x4 - 0.756 * x5,
            lambda x: x + 10,
            lambda x: x - 15
        ],
        4: [
            lambda x1, x2, x3, x4, x5: 111.742 - 1.991 * x2 - 1.991 * x4 - 0.499 * x5,
            lambda x: x + 36,
            lambda x: x - 31
        ],
        5: [
            lambda x1, x2, x3, x4, x5: 86.614 - 0.754 * x2 - 3.168 * x4 + 0.198 * x5,
            lambda x: x + 40,
            lambda x: x - 30
        ],
        6: [
            lambda x1, x2, x3, x4, x5: 69.448 + 0.164 * x2 - 2.202 * x4 + 1.687 * x5,
            lambda x: x + 32,
            lambda x: x - 22
        ],
        10: [
            lambda x1, x2, x3, x4, x5: 88.917 - 0.457 * x2 - 1.596 * x4 + 0.029 * x5,
            lambda x: x + 20,
            lambda x: x - 20
        ],
        11: [
            lambda x1, x2, x3, x4, x5: 94.313 + 0.220 * x1 - 0.739 * x2 - 2.541 * x4 - 0.882 * x5,
            lambda x: x + 18,
            lambda x: x - 24
        ],
        12: [
            lambda x1, x2, x3, x4, x5: 97.312 - 1.2 * x1 - 0.14 * x2 + 0.546 * x3 + 1.456 * x5,
            lambda x: x + 16,
            lambda x: x - 30
        ]
    },
}
