# -*- coding: utf-8 -*-
import os
import json
import psycopg2
import shapefile
import matplotlib
import numpy as np
import pandas as pd
from osgeo import osr, gdal
from adjustText import adjust_text
from matplotlib.patches import PathPatch
from matplotlib.path import Path

matplotlib.use('Agg')
import matplotlib.pyplot as plt


class StationInterpolateGridModel(object):
    shape_path = r'/home/lhtd/nm3/static/neimeng/clip_shape'

    def __init__(self, s_data, stations, factor, interpolation, polymerize, filename, region, *args, **kwargs):
        """
        初始化
        :param s_data: 源数据，站点格式
        :param stations: 站点数据
        :param factor: 要素
        :param interpolation: 格点化插值算法
        """
        self.stations = stations
        self.s_data = s_data
        self.factor = factor  # .encode("utf-8")
        self.interpolation = interpolation
        self.polymerize = polymerize
        if polymerize == 'avg' or polymerize == u'avg':
            self.polymerize = 'mean'
        self.grids = None
        self.result = None
        self.lat = None
        self.lon = None
        self.filename = filename
        self.region = region
        self.conn = psycopg2.connect(kwargs.get('dsn', '')) if kwargs.get('option', '') else kwargs.get('option', '')
        self.dsn = kwargs.get('dsn', '')
        self.option = kwargs.get('option', '')
        self.date = kwargs.get('date', '')
        self.bottom_title = kwargs.get('bottom_title', '')
        self.s_title = kwargs.get('s_title', '')
        self.station_json = kwargs.get("station_json", "result")  # Get Station Json File Name

    def clean_data(self):
        try:
            sdl = self.s_data.columns.to_list()
            idx = sdl.index(self.factor)
            self.factor = sdl[idx]
        except Exception as err:
            print(err)
        self.s_data = self.s_data.groupby(["station"]).agg({self.factor: self.polymerize}).dropna()

    def run(self, lt_pos, rb_pos, grids):
        """
        格点化插值
        :param lt_pos: 格点区域左上角坐标
        :param rb_pos: 右下角坐标
        :param grids: 格点精义 lon_size * lat_size
        :return:
        """
        self.grids = grids
        p_data = pd.merge(self.s_data, self.stations, left_on='station', right_on='code', how='inner')
        json_result = [{
            # todo : 修改经纬度顺序 2022-04-24
            # "lat": row.get("lon"),
            # "lon": row.get("lat"),
            "lon": row.get("lon"),
            "lat": row.get("lat"),
            "station_id_c": row.get("code"),
            "station_name": row.get("name"),
            "value": row.get(self.factor),
        } for idx, row in p_data.iterrows()]

        with open("{}.json".format(self.station_json), "w", encoding="utf-8") as fp:
            fp.write(json.dumps(json_result))
        del p_data["name"]

        north = p_data.sort_values(["lat"], ascending=[True]).head(1)[self.factor]
        south = p_data.sort_values(["lat"], ascending=[True]).tail(1)[self.factor]
        east = p_data.sort_values(["lon"], ascending=[True]).tail(1)[self.factor]
        west = p_data.sort_values(["lon"], ascending=[True]).head(1)[self.factor]
        p_data.loc[p_data.index[-1] + 1] = [north.values[0], "00001", 17, 112]
        p_data.loc[p_data.index[-1] + 1] = [south.values[0], "00002", 74, 112]
        p_data.loc[p_data.index[-1] + 1] = [east.values[0], "00003", 44.5, 147]
        p_data.loc[p_data.index[-1] + 1] = [west.values[0], "00004", 44.5, 77]
        lat, lon = np.meshgrid(np.linspace(lt_pos[0], rb_pos[0], grids[0]), np.linspace(lt_pos[1], rb_pos[1], grids[1]))
        self.lat, self.lon = lat, lon
        if self.interpolation[:5] == "krige":
            from pykrige.ok import OrdinaryKriging
            variogram = self.interpolation.split('_')[1]
            lat, lon = np.linspace(lt_pos[0], rb_pos[0], grids[0]), np.linspace(lt_pos[1], rb_pos[1], grids[1])
            model = OrdinaryKriging(
                list(p_data["lon"]), list(p_data["lat"]), list(p_data[self.factor]),
                variogram_model=variogram, verbose=False, enable_plotting=False, nlags=12,
                coordinates_type='geographic'
            )
            z1, ss1 = model.execute('grid', lat, lon)
            self.result = z1
        else:
            from scipy.interpolate import Rbf
            model = Rbf(
                list(p_data["lon"]), list(p_data["lat"]), list(p_data[self.factor]),
                function=self.interpolation
            )
            self.result = model(lat, lon)

        return self.result

    def post_data(self, data_type="csv"):
        save_func = {
            "csv": self.save_csv,
            "tif": self.save_tif,
            "png": self.save_png
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
        gtif_driver = gdal.GetDriverByName("GTiff")
        out_ds = gtif_driver.Create(
            self.filename, data.shape[1], data.shape[0], 1, gdal.GDT_Float32
        )
        lat_pex = (np.max(self.lat) - np.min(self.lat)) / (self.grids[0] - 1)
        lon_pex = (np.max(self.lon) - np.min(self.lon)) / (self.grids[1] - 1)
        dst_transform = (self.lat.min(), lat_pex, 0.0, self.lon.max(), 0.0, -lon_pex)
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

    def save_png(self, data):
        """
        data 格点化后的数据源
        """
        from mpl_toolkits.basemap import Basemap
        # 站点的code值
        region_code = self.region

        # 站点和数据 进行组合
        station_data = pd.merge(self.s_data, self.stations, left_on='station', right_on='code', how='inner')

        sfp = os.path.join(self.shape_path, str(region_code), str(region_code))
        # 读取 shp 文件
        sf = shapefile.Reader('%s.shp' % sfp)
        # 设置 画布
        fig = plt.figure(figsize=(8, 6))
        # 新增子区域
        ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
        # 去掉坐标轴
        ax.axis("off")
        # 读取 shapefile信息
        for sr in sf.shapeRecords():
            vertices = []
            codes = []
            pts = sr.shape.points
            prt = list(sr.shape.parts) + [len(pts)]
            for i in range(len(prt) - 1):
                for j in range(prt[i], prt[i + 1]):
                    vertices.append((pts[j][0], pts[j][1]))
                codes += [Path.MOVETO]
                codes += [Path.LINETO] * (prt[i + 1] - prt[i] - 2)
                codes += [Path.CLOSEPOLY]
            clip = Path(vertices, codes)
            clip = PathPatch(clip, transform=ax.transData)
            break
        # 缩放比例
        ow = (sf.bbox[2] - sf.bbox[0]) / 50
        aw = (sf.bbox[3] - sf.bbox[1]) / 50

        pmin, pmax = np.min(station_data[self.factor]), np.max(station_data[self.factor])
        pmin -= 0
        pmax += 0

        n_data1 = np.where(self.result > pmin, self.result, pmin)
        n_data2 = np.where(self.result < pmax, n_data1, pmax)
        n_data = n_data2

        lon_0 = (sf.bbox[0] + sf.bbox[2]) / 2
        lat_0 = (sf.bbox[1] + sf.bbox[3]) / 2

        # 底图 , 截取到 内蒙地域
        m = Basemap(
            llcrnrlon=sf.bbox[0] - ow, llcrnrlat=sf.bbox[1] - aw,
            urcrnrlon=sf.bbox[2] + ow, urcrnrlat=sf.bbox[3] + aw,
            lat_0=lat_0, lon_0=lon_0, ax=ax,
            lat_1=sf.bbox[1] - aw, lat_2=sf.bbox[3] + aw,
            lon_1=sf.bbox[0] - ow, lon_2=sf.bbox[2] + ow,
            lat_ts=0., resolution='c', no_rot=True,
            projection='cyl')  # merc, tmerc, cyl, omerc, gnom

        # 读取 市级 站点数据
        s = m.readshapefile(sfp, 'comarques', linewidth=0.1, color='blue', antialiased=True, drawbounds=True, ax=ax)

        # 对应区县站点 shapefile 文件
        for d in os.listdir(self.shape_path):
            delta = int(d) - region_code
            if not os.path.isdir(os.path.join(self.shape_path, d)) or delta <= 0:
                continue
            if delta % 100 == 0 and region_code < 150100:  # or delta < 100:
                sfp2 = os.path.join(self.shape_path, d, d)
                s2 = m.readshapefile(sfp2, 'comarques', linewidth=0.1, color='blue', antialiased=True, drawbounds=True,
                                     ax=ax)
        # x 经度 ,y 纬度
        x, y = m(self.lat, self.lon)

        # 处理 图例色卡
        if self.option:
            colors = self.option['colorList']
            valueList = self.option['valueList']
            clevs = self.option['labelList']
            cs = m.contourf(x, y, n_data, levels=valueList, antialiased=True, colors=colors, ax=ax)
        else:
            cs = m.pcolormesh(x, y, n_data, antialiased=True, alpha=0.5, cmap='coolwarm')

        # 绘制分类图
        cb = m.colorbar(cs, "left", size="3%", pad="2%")

        try:
            cs.set_clip_path(clip)
        except Exception as err:
            for ct in cs.collections:
                ct.set_clip_path(clip)

        # 图片插入 具体城市
        size_factor = 80.0
        rotation = 0
        area_station_data = station_data[self.factor]
        sql = """ select code,name,center from region """
        # to be contiune  其他城市具体
        # 内蒙古自治区 市级别
        if region_code == 150000:
            sql += " WHERE level=1 "
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
        except Exception as e:
            rows = []
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False

        # 解析rows
        if rows:
            new_texts = []
            for r_station, k in zip(rows, area_station_data):
                name = r_station[1]
                lon, lat = r_station[2]
                size = size_factor * k / pmax
                cs = m.scatter(lon, lat, s=size, marker='.', color='#D3D3D3')
                new_texts.append(plt.text(lon, lat, u"{}".format(name), va='center', rotation=rotation,
                                          fontproperties="SimHei",
                                          fontsize=9, ))
            # 修改文字覆盖
            adjust_text(new_texts, arrowprops=dict(arrowstyle='fancy', color='red', lw=1))
        xt, yt = m((np.max(self.lat) + np.min(self.lat)) / 2, np.max(self.lon))

        # plt 绘制 图片标题

        if len(self.s_title) > 0:
            plt.text(xt, yt, self.s_title, ha='center', fontproperties="SimHei", fontsize=15, fontweight='bold')
        else:
            plt.title("GIS Map")
        plt.text(xt, yt - 1, self.date, ha='center', fontproperties="SimHei", fontsize=12, )

        xt, yt = m(np.max(self.lat), np.max(self.lon))
        x0, y0 = m(np.min(self.lat), np.min(self.lon))

        ax.text(x0 + (xt - x0) * .935, yt, 'N', ha='left', va='bottom')
        ax.text(x0 + (xt - x0) * .680, yt - y0 // 2, self.bottom_title, fontproperties="SimHei", ha='left',
                va='bottom')

        ax.plot([0.95, 0.93, 0.95, 0.95, 0.97, 0.95], [0.999, 0.929, 0.964, 0.999, 0.929, 0.964], linewidth=0.4,
                color='black', zorder=1, transform=ax.transAxes)

        plt.savefig(self.filename.split('.')[0] + '.png', bbox_inches='tight', pad_inches=.3, dpi=120,
                    transparent=False)
