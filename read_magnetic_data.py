import pandas as pd
import numpy as np
import pyIGRF

import typing
import datetime
from dateutil.parser import parse


class geo_mat_point:
    def __init__(self, point_name='', point_lat=0.0, point_lon=0.0, point_alt=0.0, point_D=np.nan, point_I=np.nan,
                 point_H=np.nan, point_X=np.nan, point_Y=np.nan, point_Z=np.nan, point_F=np.nan, point_dD=np.nan,
                 point_dI=np.nan, point_dH=np.nan, point_dX=np.nan, point_dY=np.nan, point_dZ=np.nan, point_dF=np.nan):
        self.name = point_name
        self.lat = point_lat
        self.lon = point_lon
        self.alt = point_alt
        self.X = point_X
        self.Y = point_Y
        self.Z = point_Z
        self.D = point_D
        self.Ii = point_I
        self.H = point_H
        self.F = point_F
        self.dX = point_dX
        self.dY = point_dY
        self.dZ = point_dZ
        self.dD = point_dD
        self.dI = point_dI
        self.dH = point_dH
        self.dF = point_dF

def datetime2yeardec(time: typing.Union[str, datetime.datetime, datetime.date]) -> float:
    """
    Convert a datetime into a float. The integer part of the float should
    represent the year.
    Order should be preserved. If adate<bdate, then d2t(adate)<d2t(bdate)
    time distances should be preserved: If bdate-adate=ddate-cdate then
    dt2t(bdate)-dt2t(adate) = dt2t(ddate)-dt2t(cdate)
    """

    if isinstance(time, float):
        # assume already year_dec
        return time
    if isinstance(time, str):
        t = parse(time)
    elif isinstance(time, datetime.datetime):
        t = time
    elif isinstance(time, datetime.date):
        t = datetime.datetime.combine(time, datetime.datetime.min.time())
    elif isinstance(time, (tuple, list, np.ndarray)):
        return np.asarray([datetime2yeardec(t) for t in time])
    else:
        raise TypeError("unknown input type {}".format(type(time)))

    year = t.year

    boy = datetime.datetime(year, 1, 1)
    eoy = datetime.datetime(year + 1, 1, 1)

    return year + ((t - boy).total_seconds() / ((eoy - boy).total_seconds()))

def read_dat(t_path):
    point_list = []
    with open(t_path, 'rb') as f:
        line_str = f.readline()
        line_str_list = line_str.decode().strip().split(',')
        # while line_str:
        #     pass

    df = pd.read_csv(t_path, header=None, index_col=None)
    df.columns = ['点名', '经度', '纬度', '海拔', '通化台站', '通化日期', '通化起始时间', '通化截至时间', 'F', '观测日期', '观测开始时间', 'unused01',
                  'unused02', '观测结束时间', '通化值', '通化均方差', 'unused03', 'unused04', 'unused05', 'unused06']
    # df.index =df['点名']

    return df


dat_path = r'E:\Python\日变通化标准数据集_云南测点-闫万生和毛丰龙_2.dat'
observation_F_df = read_dat(dat_path)
out_str = '点  名 ,  经  度 ,  纬  度  , 海拔,  D       ,  I       ,    H     ,    X     ,     Y    ,     Z    ,' \
          '    F     ,   dD     ,  dI      ,  dH      ,  dX      ,    dY    ,   dZ     ,  dF\n'

for i in observation_F_df.index:
    lat = observation_F_df.loc[i, ['纬度']].values[0, ]
    lon = observation_F_df.loc[i, ['经度']].values[0, ]
    alt = observation_F_df.loc[i, ['海拔']].values[0, ] * 0.001
    th_date = datetime2yeardec(observation_F_df.loc[i, ['通化日期']].values[0, ])
    cal_val = pyIGRF.igrf_value(lat, lon, alt, th_date)
    variation = pyIGRF.igrf_variation(lat, lon, alt, th_date)
    # out_str-= df.loc[i, ['点名']].values[0,]+','+str(cal_val[0])
    out_str += observation_F_df.loc[i, ['点名']].values[0, ].strip() + ',' + str(format(lon, '>10.6f')) + ',' + str(
        format(lat, '>9.6f')) + ',' + str(format(alt * 1000, '>5.0f')) + ',' + ','.join(
        str(format(tup, '<10.4f')) for tup in cal_val) + ',' + ','.join(
        str(format(tup2, '<10.4f')) for tup2 in variation) + '\n'

main_magnetic_out_path = '\\'.join(dat_path.split('\\')[:-1]) + '\\' + dat_path.split('\\')[-1][:-4] + '_主磁场.dat'
with open(main_magnetic_out_path, 'w', encoding='utf-8') as write_f:
    write_f.write(out_str)

main_magnetic_df = pd.read_csv(main_magnetic_out_path,header=0,index_col=None)

lithospheric_df = observation_F_df
lithospheric_df.drop(['unused01', 'unused02',  '通化起始时间', '通化截至时间','unused03', 'unused04', 'unused05', 'unused06'], axis=1, inplace=True)
lithospheric_df['主磁场'] = main_magnetic_df[main_magnetic_df.columns.tolist()[10]]
lithospheric_df['岩石圈'] = lithospheric_df['通化值']-lithospheric_df['主磁场']

lithospheric_out_path = main_magnetic_out_path[:-7]+'岩石圈磁场.dat'
lithospheric_df.to_csv(lithospheric_out_path,index=False)
print('运行结束')