#!/usr/bin/python
# -*- coding: utf-8 -*-

import cPickle as pickle
from core import app


def save_object(obj, file_path):
    f = file(file_path, 'wb')
    pickle.dump(obj, f, True)
    f.close()
    print("%s saved successfully!" % file_path)


def load_object(file_path):
    f = file(file_path, 'rb')
    obj = pickle.load(f)
    print("%s loaded successfully!" % file_path)
    f.close()
    return obj


def normalize(weight_value, weight_min, weight_max):
    # 根据 该特征字段 的 最大最小值 计算当前取值 的 归一化值
    v_normalized = (weight_value - weight_min) / (weight_max - weight_min)
    if v_normalized > 1:
        return 1.0
    elif v_normalized < 0:
        return 0.0
    else:
        return v_normalized


def get_feedback_city_poi_list(feedback_city_poi_id_dict):
    """将city_id - poi_name - poi_id 的两层dict转换成 city_id - poi_id 的一层dict

    :param feedback_city_poi_id_dict:
    :return:
    """
    feedback_city_poi_dict = {}

    for city_id in feedback_city_poi_id_dict:
        feedback_city_poi_dict[city_id] = []
        for poi_name in feedback_city_poi_id_dict[city_id]:
            feedback_city_poi_dict[city_id].extend(feedback_city_poi_id_dict[city_id][poi_name])

    return feedback_city_poi_dict


if __name__ == '__main__':
    # 城市站反馈问题receiver_poi
    FEEDBACK_CITY_LIST = app.config.get('FEEDBACK_CITY_LIST', [])
    FEEDBACK_CITY_POI_ID_DICT = app.config.get("FEEDBACK_CITY_POI_IDS", 0.3)
    FEEDBACK_CITY_POI_ID_LIST = get_feedback_city_poi_list(FEEDBACK_CITY_POI_ID_DICT)
    print FEEDBACK_CITY_POI_ID_LIST
    pass
