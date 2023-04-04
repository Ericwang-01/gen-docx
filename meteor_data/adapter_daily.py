# -*- coding: utf-8 -*-
import pandas as pd
from .adapter_base import MeteorBaseAdapter


class MeteorDataDailyAdapter(MeteorBaseAdapter):
    def query(self, fields, period):
        sql = """
    SELECT station_id_c as station, to_char(datetime, 'YYYY-MM-DD') AS date, {0}
    FROM meteo_surf_day_nm
    WHERE station_id_c IN ('{1}') AND datetime BETWEEN '{2}'
        """.format(",".join(fields), "','".join(self.stations), "' AND '".join(period))

        cursor = self.db_connect.cursor()
        cursor.execute(sql)
        labels = [str(row[0]) for row in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame([
            [float(row[i]) if i > 1 else row[i] for i in range(len(labels))] for row in rows
        ], columns=labels)

        m = df > df
        m['date'] = False
        for k in labels[2:]:
            m[k] = df[k] > 3000.0
        return df.mask(m)
