# -*- coding: utf-8 -*-


def tem_color(x):
    """
    温度图例
    :param x:
    :return:
    """
    if x < 0:
        return low_tem_color(x)
    else:
        return high_tem_color(x)


def low_tem_color(x):
    if -2 <= x < 0:
        return "#97E8AD"
    elif -4 <= x < -2:
        return "#98D6C4"
    elif -6 <= x < -4:
        return "#99CDD0"
    elif -8 <= x < -6:
        return "#9AC4DC"
    elif -10 <= x < -8:
        return "#9BBCE8"
    elif -12 <= x < -10:
        return "#87AFE5"
    elif -14 <= x < -12:
        return "#74A3E2"
    elif -16 <= x < -14:
        return "#6196E0"
    elif -18 <= x < -16:
        return "#4E8ADD"
    elif -20 <= x < -18:
        return "#3B7EDB"
    elif -22 <= x < -20:
        return "#306AC7"
    elif -24 <= x < -22:
        return "#2657B3"
    elif -26 <= x < -24:
        return "#1B449F"
    elif -28 <= x < -26:
        return "#11318B"
    elif -30 <= x < -28:
        return "#071E78"
    elif x < -30:
        return "#020C64"


def high_tem_color(x):
    if 0 <= x < 2:
        return "#D7DE7E"
    elif 2 <= x < 4:
        return "#EADB70"
    elif 4 <= x < 6:
        return "#F4D963"
    elif 6 <= x < 8:
        return "#FACC4F"
    elif 8 <= x < 10:
        return "#F7B42D"
    elif 10 <= x < 12:
        return "#F29B00"
    elif 12 <= x < 14:
        return "#F19303"
    elif 14 <= x < 16:
        return "#F0840A"
    elif 16 <= x < 18:
        return "#EF7511"
    elif 18 <= x < 20:
        return "#EE6618"
    elif 20 <= x < 22:
        return "#EE581F"
    elif 22 <= x < 24:
        return "#E74B1A"
    elif 24 <= x < 26:
        return "#E03F16"
    elif 26 <= x < 28:
        return "#D93312"
    elif 28 <= x < 30:
        return "#D0240E"
    elif 30 <= x < 32:
        return "#C20003"
    elif 32 <= x < 34:
        return "#B50109"
    elif 34 <= x < 36:
        return "#A90210"
    elif 36 <= x < 38:
        return "#8A0519"
    elif 38 <= x < 40:
        return "#6F0015"
    elif x >= 40:
        return "#50000F"


def pre_color(x):
    """
    降水图例
    :param x:
    :return:
    """
    if x < 1:
        return "#FFFFFF"
    elif 1 <= x < 10:
        return "#CFFFCF"
    elif 10 <= x < 25:
        return "#00FF00"
    elif 25 <= x < 50:
        return "#33CC33"
    elif 50 <= x < 100:
        return "#009999"
    elif 100 <= x < 200:
        return "#008200"
    elif 200 <= x < 400:
        return "#0096FF"
    elif 400 <= x < 800:
        return "#0000FF"
    elif x >= 800:
        return "#FA00FF"


def pre_r_color(x):
    """
    降水距平图例
    :param x:
    :return:
    """
    if x < 50:
        return "#FF9966"
    if -50 <= x < 0:
        return "#FFFF00"
    if 0 <= x < 50:
        return "#00FF00"
    if 50 <= x < 100:
        return "#009999"
    if 100 <= x < 200:
        return "#0096FF"
    if x >= 200:
        return "#0000FF"
