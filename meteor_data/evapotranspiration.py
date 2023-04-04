# -*- coding: Utf-8 -*-
import math
import numpy as np
from datetime import datetime


class BasicParameter:
    @staticmethod
    def date_to_day_of_year(my_date):
        """
        get day sequence of year
        :param my_date:
        :return:
        """
        fmt = '%Y-%m-%d'
        dt = datetime.strptime(str(my_date), fmt)
        tt = dt.timetuple()
        return tt.tm_yday

    @staticmethod
    def sun_rise_time(my_date, latitude):
        """
        get sun rise time and sunshine length
        :param latitude: 纬度
        :param my_date:日期
        :return: 太阳升起时间  可照时数 大气上届太阳辐射
        """
        j = BasicParameter.date_to_day_of_year(my_date)
        dr = 1 + 0.033 * math.cos(2 * math.pi * j / 365)
        delta_solar = 0.409 * math.sin(2 * math.pi * j / 365 - 1.39)
        omga = math.acos(-math.tan(latitude / 180 * math.pi) * math.tan(delta_solar))
        sun_rise = round(12 - 12 * omga / math.pi, 4)
        sunshine_length = round(24 * omga / math.pi, 4)
        ra = 118.08 * dr * (omga * math.sin(latitude / 180 * math.pi) * math.sin(delta_solar) + math.cos(
                latitude / 180 * math.pi) * math.cos(delta_solar) * math.sin(omga)) / math.pi
        return sun_rise, sunshine_length, ra

    @staticmethod
    def get_solar_radiation(my_date, sunshine_hours, latitude):
        """
        get solar radiation
        :param sunshine_hours: ssh
        :param latitude: 纬度
        :param my_date:日期
        :return: 无遮挡辐射量(晴空辐射)  太阳总辐射
        """
        ra = BasicParameter.sun_rise_time(my_date, latitude)[2]
        solar_radiation_ra = (0.25 + 0.5 * sunshine_hours / BasicParameter.sun_rise_time(my_date, latitude)[1])
        solar_radiation = ra * solar_radiation_ra
        solar_radiation = round(solar_radiation, 4)
        return solar_radiation_ra, solar_radiation


class EvapotranspirationSingle:
    def __init__(self, latitude, elevation, wind_sensor_height):
        self.latitude = latitude  # float degree
        self.elevation = elevation  # m
        self.a_constant = 0.25
        self.b_constant = 0.50
        self.planetary_albedo = 0.23
        self.wind_sensor_height = wind_sensor_height  # m

    def hargreaves(self, my_date, t_max, t_min):
        """
        max_temperature,min_temperature, [mean_temperature]
        :return:
        """
        t_mean = (t_max + t_min) / 2
        basic_parameter = BasicParameter()
        evapotranspiration_0 = 0.0023 * basic_parameter.sun_rise_time(my_date, self.latitude)[2] * (
            t_mean + 17.8) * (t_max - t_min) ** 0.5
        if evapotranspiration_0 < 0.0:
            evapotranspiration_0 = 0.01
        elif evapotranspiration_0 > 15.0:
            evapotranspiration_0 = 15.0
        return evapotranspiration_0

    def priestley_taylor(self, my_date, t_max, t_min, rh, ssh):
        """
        max_temperature,min_temperature, relative_humidity, sunshine_hours
        elevation
        :return:
        """
        k_wind = 1.26
        ground_heat = 0.0

        t_mean = (t_max + t_min) / 2
        k_es_t = 4098 * 0.6108 * math.exp(17.27 * t_mean / (t_mean + 237.3)) / (t_mean + 237.3) ** 2

        lambda_water_latent_heat = 2.501 - 0.002361 * t_mean
        pressure_a = 101.3 * ((293 - 0.0065 * self.elevation) / 293) ** 5.26

        gama_dry_wet_const = 0.665 * 10 ** -3 * pressure_a

        es_t_max = 0.6108 * math.exp(17.27 * t_max / (t_max + 237.3))
        es_t_min = 0.6108 * math.exp(17.27 * t_min / (t_min + 237.3))
        es = (es_t_max + es_t_min) / 2
        ea = 0.005 * rh * (es_t_max + es_t_min)

        basic_parameter = BasicParameter()
        solar_radiation_ra = basic_parameter.get_solar_radiation(my_date, ssh, self.latitude)

        rn_s = (1 - self.planetary_albedo) * solar_radiation_ra[1]  #
        rn_s0 = (0.75 + 2 * 10 ** -5 * self.elevation) * basic_parameter.sun_rise_time(my_date, self.latitude)[2]
        rs = solar_radiation_ra[1]
        rn_l = (2.4515 * 10 ** -9) * ((t_max + 273.16) ** 4 + (t_min + 273.16) ** 4) * (0.34 - 0.14 * math.sqrt(ea)) * (
            1.35 * rs / rn_s0 - 0.35)  #
        rn = rn_s - rn_l

        evapotranspiration_0 = k_wind * k_es_t * (rn - ground_heat) / (lambda_water_latent_heat * (
            k_es_t + gama_dry_wet_const))

        if evapotranspiration_0 < 0.0:
            evapotranspiration_0 = 0.01
        elif evapotranspiration_0 > 15.0:
            evapotranspiration_0 = 15.0

        return evapotranspiration_0

    def penman_monteith(self, my_date, t_max, t_min, rh, ssh, wind_speed):
        """
        max_temperature,min_temperature,relative_humidity, sunshine_hours, wind_speed_10m
        elevation
        height of wind speed sensor
        :return:
        """
        ground_heat = 0.0

        t_mean = (t_max + t_min) / 2
        k_es_t = 4098 * 0.6108 * math.exp(17.27 * t_mean / (t_mean + 237.3)) / (t_mean + 237.3) ** 2

        lambda_water_latent_heat = 2.501 - 0.002361 * t_mean
        pressure_a = 101.3 * ((293 - 0.0065 * self.elevation) / 293) ** 5.26

        gama_dry_wet_const = 0.665 * 10 ** -3 * pressure_a

        es_t_max = 0.6108 * math.exp(17.27 * t_max / (t_max + 237.3))
        es_t_min = 0.6108 * math.exp(17.27 * t_min / (t_min + 237.3))
        es = (es_t_max + es_t_min) / 2
        ea = 0.005 * rh * (es_t_max + es_t_min)

        basic_parameter = BasicParameter()
        solar_radiation_ra = basic_parameter.get_solar_radiation(my_date, ssh, self.latitude)

        rn_s = (1 - self.planetary_albedo) * solar_radiation_ra[1]  #
        rn_s0 = (0.75 + 2 * 10 ** -5 * self.elevation) * basic_parameter.sun_rise_time(my_date, self.latitude)[2]
        rs = solar_radiation_ra[1]
        rn_l = (2.4515 * 10 ** -9) * ((t_max + 273.16) ** 4 + (t_min + 273.16) ** 4) * (0.34 - 0.14 * math.sqrt(ea)) * (
            1.35 * rs / rn_s0 - 0.35)  #
        rn = rn_s - rn_l

        evapotranspiration_0 = (0.408 * k_es_t * (rn - ground_heat) + 900 * gama_dry_wet_const * (
            0.72 * wind_speed) * (es - ea) / (t_mean + 273)) / (
                                   k_es_t + gama_dry_wet_const * (1 + 0.34 * 0.72 * wind_speed))

        if evapotranspiration_0 < 0.0:
            evapotranspiration_0 = 0.01
        elif evapotranspiration_0 > 15.0:
            evapotranspiration_0 = 15.0

        return evapotranspiration_0


class EvapotranspirationMultiDate:
    def __init__(self, weather_data, latitude, elevation, wind_sensor_height):
        self.weather_data = np.array(weather_data)  # date, t_max, t_min, rh, ssh, wind_speed: string type
        self.latitude = latitude  # float degree
        self.elevation = elevation  # m
        self.a_constant = 0.25
        self.b_constant = 0.50
        self.planetary_albedo = 0.23
        self.wind_sensor_height = wind_sensor_height  # m

    def cal_et0_pm(self):
        column_num = self.weather_data.shape[1]
        row_num = self.weather_data.shape[0]

        cal_data = np.ones((row_num, 1))
        cal_data_str = cal_data.astype(np.str)
        cal_et0 = EvapotranspirationSingle(self.latitude, self.elevation, 10)
        for i in range(0, row_num, 1):
            pm = cal_et0.penman_monteith(self.weather_data[i, 0], float(self.weather_data[i, 1]),
                                         float(self.weather_data[i, 2]), float(self.weather_data[i, 3]),
                                         float(self.weather_data[i, 4]), float(self.weather_data[i, 5]))
            cal_data_str[i] = str(pm)
        cal_data_str = np.hstack((self.weather_data, cal_data_str))
        return cal_data_str


if __name__ == '__main__':
    # print("sun rise time")
    # print(et.sun_rise_time('2017-01-01', 37.2)[0])
    # print("length of day time")
    # print(et.sun_rise_time('2017-01-01', 37.2)[1])
    # print("solar radiation on top of atmosphere")
    # print(et.sun_rise_time('2017-01-01', 37.2)[2])
    # print("solar radiation")
    # print(et.get_solar_radiation('2017-01-01', 0, 37.2)[1])
    #
    # get et0 via three methods
    et0 = EvapotranspirationSingle(37.2, 11.5, 10)

    hglef = et0.hargreaves('2017-1-1', 20, 15)
    print("hglef")
    print(hglef)

    prt = et0.priestley_taylor('2017-1-1', 20, 15, 45, 0)
    print("Priestley-Taylor")
    print(prt)

    pm = et0.penman_monteith('2017-1-1', 20, 15, 45, 0, 5)
    print("Penman-Monteith:")
    print(pm)

    # get et0 by multi data   日期 最高气温 最低气温 相对湿度 日照时数 10风速
    multi_data = [['2017-1-1', 20, 15, 45, 10, 5],
                  ['2017-1-2', 20, 15, 45, 10, 5],
                  ['2017-1-3', 20, 15, 45, 10, 5],
                  ['2017-1-4', 20, 15, 45, 10, 5],
                  ['2017-1-5', 20, 15, 45, 10, 5],
                  ['2017-1-6', 20, 15, 45, 10, 5]]
    et_test = EvapotranspirationMultiDate(multi_data, 37.2, 11.5, 10)
    result = et_test.cal_et0_pm()
    print("ET0 of multi day:")
    print(result)
