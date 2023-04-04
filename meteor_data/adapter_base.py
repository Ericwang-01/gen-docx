# -*- coding: utf-8 -*-
from abc import abstractmethod


class MeteorBaseAdapter:
    def __init__(self, stations, db_connect):
        """
        构造函数
        :param stations 站点列表
        :param db_connect 数据库连接句柄
        """
        self.stations = stations
        self.db_connect = db_connect

    @abstractmethod
    def query(self, fields, period):
        """
        检索数据
        :param fields 字段列表
        :param period 起止时间区间
        :return DataFrame
        """
        pass
