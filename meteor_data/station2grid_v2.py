# -*- coding: utf-8 -*-
"""
Station Convert Grid Version 2.0
@author: xy ning
@create_date: 2022-04-24
@last_modified: 2022-04-24
"""
import json
import numpy as np
import pandas as pd
from osgeo import osr

try:
    import gdal
except ImportError:
    from osgeo import gdal


class StationInterpolateGridModel(object):

    def __init__(self, s_data, stations, factor, interpolation, polymerize, filename, **kwargs):
        """
        初始化
        :param s_data: 源数据，站点格式
        :param stations: 站点数据
        :param factor: 要素
        :param interpolation: 格点化插值算法
        """
        self.stations = stations
        self.s_data = s_data
        self.factor = factor
        self.interpolation = interpolation
        self.polymerize = "mean" if polymerize == 'avg' or polymerize == u'avg' else polymerize
        self.grids = None
        self.result = None
        self.lat = None
        self.lon = None
        self.filename = filename
        self.station_json = kwargs.get("station_json", "result")  # Get Station Json File Name
        self.method = kwargs.get("method", "standard")

    def clean_data(self):
        # try:
        sdl = self.s_data.columns.to_list()
        idx = sdl.index(self.factor)
        self.factor = sdl[idx]
        # except Exception as err:
        #     print(err)
        if self.method == "import":
            self.s_data = self.s_data.groupby(["lat", "lon"]).agg({self.factor: self.polymerize}).dropna()
        else:
            self.s_data = self.s_data.groupby(["station"]).agg({self.factor: self.polymerize}).dropna()

    def write_json_data(self, p_data):
        json_result = [{
            "lat": row.get("lat"),
            "lon": row.get("lon"),
            "station_id_c": row.get("code"),
            "station_name": row.get("name"),
            "value": row.get(self.factor),
        } for idx, row in p_data.iterrows()]

        with open("{}.json".format(self.station_json), "w", encoding="utf-8") as fp:
            fp.write(json.dumps(json_result))

    def add_max_point(self, p_data):
        """
        添加四方位点 优化插值
        @param p_data:
        @return:
        """
        south = p_data.sort_values(["lat"], ascending=[True]).head(1)[self.factor]
        north = p_data.sort_values(["lat"], ascending=[True]).tail(1)[self.factor]
        east = p_data.sort_values(["lon"], ascending=[True]).tail(1)[self.factor]
        west = p_data.sort_values(["lon"], ascending=[True]).head(1)[self.factor]
        p_data.loc[p_data.index[-1] + 1] = [north.values[0], 74, 112]
        p_data.loc[p_data.index[-1] + 1] = [south.values[0], 17, 112]
        p_data.loc[p_data.index[-1] + 1] = [east.values[0], 44.5, 147]
        p_data.loc[p_data.index[-1] + 1] = [west.values[0], 44.5, 77]

        return p_data

    def run(self, lt_pos, rb_pos, grids):
        """
        格点化插值
        :param lt_pos: 格点区域左上角坐标
        :param rb_pos: 右下角坐标
        :param grids: 格点精义 lon_size * lat_size
        :return:
        """
        self.grids = grids
        if self.method == "import":
            p_data = self.s_data.reset_index()
        else:
            p_data = pd.merge(self.s_data, self.stations, left_on='station', right_on='code', how='inner')
        self.write_json_data(p_data)
        if "name" in p_data.columns.to_list():
            del p_data["name"]
        if "code" in p_data.columns.to_list():
            del p_data["code"]

        lon = np.linspace(lt_pos[0], rb_pos[0], grids[0])
        lat = np.linspace(lt_pos[1], rb_pos[1], grids[1])
        self.lon, self.lat = np.meshgrid(lon, lat)
        if self.interpolation[:5] == "krige":
            from pykrige.ok import OrdinaryKriging
            variogram = self.interpolation.split('_')[1]
            model = OrdinaryKriging(
                list(p_data["lon"]), list(p_data["lat"]), list(p_data[self.factor]),
                variogram_model=variogram, verbose=False, enable_plotting=False, nlags=12,
                coordinates_type='geographic'
            )
            z1, ss1 = model.execute('grid', lon, lat)
            self.result = z1
        elif self.interpolation == 'cressman':
            # cressman插值，按站点密集程度将区域分为左、中、右上、右下四部分
            from metpy.interpolate import inverse_distance_to_grid, interpolate_to_grid
            # p_data = self.add_max_point(p_data)

            # 北纬47以北
            sn_rate = (lt_pos[1]-48)/(lt_pos[1]-rb_pos[1])
            n_lat = np.linspace(lt_pos[1], 48, round(grids[1] * sn_rate))
            n_lon_m, n_lat_m = np.meshgrid(lon, n_lat)
            n_result = inverse_distance_to_grid(
                xp=p_data['lon'].values,
                yp=p_data['lat'].values,
                variable=p_data[self.factor].values,
                grid_x=n_lon_m,
                grid_y=n_lat_m,
                r=2.8, 
                min_neighbors=1
            )
            n_result[np.isnan(n_result)] = 0

            # 北纬47以南
            s_lat = np.linspace(48, rb_pos[1], round(grids[1] * (1-sn_rate)))
            # 东经103以西
            ww_lon = np.linspace(lt_pos[0], 103, round(grids[0] * (103-lt_pos[0])/(rb_pos[0]-lt_pos[0])))
            ww_lon_m, ww_lat_m = np.meshgrid(ww_lon, s_lat)
            ww_result = inverse_distance_to_grid(
                xp=p_data['lon'].values,
                yp=p_data['lat'].values,
                variable=p_data[self.factor].values,
                grid_x=ww_lon_m,
                grid_y=ww_lat_m,
                r=4, 
                min_neighbors=1
            )
            ww_result[np.isnan(ww_result)] = 0

            # 北纬47以南，东经103以东110以西
            w_lon = np.linspace(103, 110, round(grids[0] * ((110-103)/(rb_pos[0]-lt_pos[0]))))
            w_lon_m, w_lat_m = np.meshgrid(w_lon, s_lat)
            w_result = inverse_distance_to_grid(
                xp=p_data['lon'].values,
                yp=p_data['lat'].values,
                variable=p_data[self.factor].values,
                grid_x=w_lon_m,
                grid_y=w_lat_m,
                r=2.8, 
                min_neighbors=1
            )
            w_result[np.isnan(w_result)] = 0

            # 北纬47以南，东经110以东118以西
            e_lon = np.linspace(110, 118, round(grids[0] * ((118-110)/(rb_pos[0]-lt_pos[0]))))
            # 北纬42.5以北
            sn_e_rate = (48-42.5)/(48-rb_pos[1])
            e_n_lat = np.linspace(48, 42.5, round((grids[1]-n_result.shape[0]) * sn_e_rate))
            e_n_lon_m, e_n_lat_m = np.meshgrid(e_lon, e_n_lat)
            e_n_result = inverse_distance_to_grid(
                xp=p_data['lon'].values,
                yp=p_data['lat'].values,
                variable=p_data[self.factor].values,
                grid_x=e_n_lon_m,
                grid_y=e_n_lat_m,
                r=2.5, 
                min_neighbors=1
            )
            e_n_result[np.isnan(e_n_result)] = 0

            # 北纬42.5以南
            e_s_lat = np.linspace(42.5, rb_pos[1], round((grids[1]-n_result.shape[0]) * (1-sn_e_rate)))
            e_s_lon_m, e_s_lat_m = np.meshgrid(e_lon, e_s_lat)
            e_s_result = inverse_distance_to_grid(
                xp=p_data['lon'].values,
                yp=p_data['lat'].values,
                variable=p_data[self.factor].values,
                grid_x=e_s_lon_m,
                grid_y=e_s_lat_m,
                r=1.5, 
                min_neighbors=1
            )
            e_s_result[np.isnan(e_s_result)] = 0
            e_result = np.concatenate([e_n_result, e_s_result], axis=0)

            # 北纬47以南，东经118以东
            ee_lon = np.linspace(118, rb_pos[0], round(grids[0] * ((rb_pos[0]-118)/(rb_pos[0]-lt_pos[0]))))
            ee_lon_m, ee_lat_m = np.meshgrid(ee_lon, s_lat)
            ee_result = inverse_distance_to_grid(
                xp=p_data['lon'].values,
                yp=p_data['lat'].values,
                variable=p_data[self.factor].values,
                grid_x=ee_lon_m,
                grid_y=ee_lat_m,
                r=1.4, 
                min_neighbors=1
            )
            ee_result[np.isnan(ee_result)] = 0

            s_result = np.concatenate([ww_result, w_result, e_result, ee_result], axis=1)
            self.result = np.concatenate([n_result, s_result], axis=0)

            # # 东经104以西的部分
            # left_lon = np.linspace(lt_pos[0], 104, round(grids[0] * (104-lt_pos[0])/(rb_pos[0]-lt_pos[0])))
            # left_lon_m, left_lat_m = np.meshgrid(left_lon, lat)
            # left_result = inverse_distance_to_grid(
            #     xp=p_data['lon'].values,
            #     yp=p_data['lat'].values,
            #     variable=p_data[self.factor].values,
            #     grid_x=left_lon_m,
            #     grid_y=left_lat_m,
            #     r=4.5, 
            #     min_neighbors=1
            # )
            # left_result[np.isnan(left_result)] = 0

            # # 东经104-119的部分
            # center_lon = np.linspace(104, 119, round(grids[0] * (119-104)/(rb_pos[0]-lt_pos[0])))
            # center_lon_m, center_lat_m = np.meshgrid(center_lon, lat)
            # center_result = inverse_distance_to_grid(
            #     xp=p_data['lon'].values,
            #     yp=p_data['lat'].values,
            #     variable=p_data[self.factor].values,
            #     grid_x=center_lon_m,
            #     grid_y=center_lat_m,
            #     r=1.6, 
            #     min_neighbors=1
            # )
            # center_result[np.isnan(center_result)] = 0

            # # 东经119以东，北纬49以北的部分
            # right_lon = np.linspace(119, rb_pos[0], round(grids[0] * (rb_pos[0]-119)/(rb_pos[0]-lt_pos[0])))
            # right_top_lat = np.linspace(lt_pos[1], 49, round(grids[1] * (49-lt_pos[1])/(rb_pos[1]-lt_pos[1])))
            # right_top_lon_m, right_top_lat_m = np.meshgrid(right_lon, right_top_lat)
            # right_top_result = inverse_distance_to_grid(
            #     xp=p_data['lon'].values,
            #     yp=p_data['lat'].values,
            #     variable=p_data[self.factor].values,
            #     grid_x=right_top_lon_m,
            #     grid_y=right_top_lat_m,
            #     r=3, 
            #     min_neighbors=1
            # )
            # right_top_result[np.isnan(right_top_result)] = 0

            # # 东经119以东，北纬49以南的部分
            # right_bottom_lat = np.linspace(49, rb_pos[1], round(grids[1] * (rb_pos[1]-49)/(rb_pos[1]-lt_pos[1])))
            # right_bottom_lon_m, right_bottom_lat_m = np.meshgrid(right_lon, right_bottom_lat)
            # right_bottom_result = inverse_distance_to_grid(
            #     xp=p_data['lon'].values,
            #     yp=p_data['lat'].values,
            #     variable=p_data[self.factor].values,
            #     grid_x=right_bottom_lon_m,
            #     grid_y=right_bottom_lat_m,
            #     r=1.3, 
            #     min_neighbors=1
            # )
            # right_bottom_result[np.isnan(right_bottom_result)] = 0
            # # 拼接右上右下两部分
            # right_result = np.concatenate([right_top_result, right_bottom_result], axis=0)

            # # 拼接完整区域
            # self.result = np.concatenate([left_result, center_result, right_result], axis=1)
            
        else:
            from scipy.interpolate import Rbf
            if self.interpolation == "linear":
                p_data = self.add_max_point(p_data)
            model = Rbf(
                list(p_data["lon"]), list(p_data["lat"]), list(p_data[self.factor]),
                function=self.interpolation
            )
            self.result = model(self.lon, self.lat)

        return self.result

    def post_data(self, data_type="csv"):
        save_func = {
            "csv": self.save_csv,
            "tif": self.save_tif,
        }
        return save_func[data_type](self.result)

    def save_csv(self, data):
        data.to_csv(self.filename)
        return data

    def save_tif(self, data):
        """
        写入tif
        :param data: 数据
        :return:
        """
        data = np.array(data, dtype="float")
        nodata = np.asarray(0, dtype="float")
        tif_driver = gdal.GetDriverByName("GTiff")
        out_ds = tif_driver.Create(self.filename, data.shape[1], data.shape[0], 1, gdal.GDT_Float32)
        lon_pex = (np.max(self.lon) - np.min(self.lon)) / (self.grids[0] - 1)
        lat_pex = (np.max(self.lat) - np.min(self.lat)) / (self.grids[1] - 1)
        dst_transform = (self.lon.min(), lon_pex, 0.0, self.lat.max(), 0.0, -lat_pex)
        # 设置裁剪出来图的原点坐标
        out_ds.SetGeoTransform(dst_transform)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        if srs is not None:
            # 设置SRS属性（投影信息）
            out_ds.SetProjection(str(srs))
        out_ds.GetRasterBand(1).WriteArray(data)
        out_ds.GetRasterBand(1).SetNoDataValue(float(nodata))
        # 将缓存写入磁盘
        out_ds.FlushCache()
        print("FlushCache succeed")
        del out_ds
