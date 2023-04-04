# encoding:utf-8
def get_win_direction(win_d):
    """
    根据风向角度判断风向
    :param win_d: float, 风向角度
    :return: win_d_str: str, 风向
    """
    win_direction_dict = {
        "东北风": [11.26, 78.75],
        "东风": [78.76, 101.25],
        "东南风": [101.26, 168.75],
        "南风": [168.76, 191.25],
        "西南风": [191.26, 258.75],
        "西风": [258.76, 281.25],
        "西北风": [281.26, 348.76],
    }
    print('看看字典的元素\n', win_direction_dict.items)
    for k, v in win_direction_dict.items():
        if win_d >= 348.76 and  win_d <= 11.25:
            return "北风"
        elif v[0] <= win_d and  win_d <= v[1]:
            return k
result= get_win_direction(3000)
print(result)