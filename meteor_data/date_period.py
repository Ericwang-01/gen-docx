# -*- coding: utf-8 -*-

import datetime


class DatePeriod:
    @staticmethod
    def in_date(str_datetime):
        return str_datetime

    @staticmethod
    def in_pentad(str_datetime):
        """
        日期转换为所在候
        :param str_datetime:
        :return:
        """
        y, m, d = [int(x) for x in str_datetime.split("-")][:3]
        return '%s-%s-%d' % (y, m, int((d + 4) / 5) - int(d / 31))

    @staticmethod
    def in_i10days(str_datetime):
        """
        日期转换为所在旬
        :param str_datetime:
        :return:
        """
        y, m, d = [int(x) for x in str_datetime.split("-")][:3]
        return '%d-%02d-%d' % (y, m, int((d + 9)/10) - int(d / 31))

    @staticmethod
    def in_doy(str_datetime):
        """
        日期转换为所在年的第多少天
        :param str_datetime:
        :return:
        """
        return (
                datetime.datetime.strptime(str_datetime, "%Y-%m-%d") -
                datetime.datetime.strptime('%s-01-01' % str_datetime[:4], "%Y-%m-%d")
        ).days + 1

    @staticmethod
    def in_month(str_datetime):
        return str_datetime[5:7]

    @staticmethod
    def in_part(str_datetime, part_size):
        func = {
            "daily": DatePeriod.in_date,
            "pentad": DatePeriod.in_pentad,
            "i10days": DatePeriod.in_i10days,
            "doy": DatePeriod.in_doy,
            "month": DatePeriod.in_month
        }
        return func[part_size](str_datetime)
