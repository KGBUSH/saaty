#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 xuekun.zhuang <zhuangxuekun@imdada.cn>


import os
import geohash
from core import app
from core import cache
from saaty.utils.utils import save_object, load_object, normalize
from saaty.constants import cache_keys
from saaty.constants import cache_expire
from saaty.models.poi_time_difficulty import POIReceiverTimeDifficulty
from saaty.models.poi_time_difficulty import POISupplierTimeDifficulty

__all__ = [
    'get_poi_latency_score',
    'get_latency_delta',
    'get_poi_latency_difficulty'
]

# 初始化LR权重模型映射文件
PROJECT_PATH = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir))

# 骑士反馈问题receiver_poi
courier_feedback_poi_dict = load_object(PROJECT_PATH + "/resource_data/courier_feedback_receiver_geohash.pkl")

# M2模型专用
supplier_id_weight_dict = load_object(PROJECT_PATH + "/resource_data/supplier_id_weight_dict.0.pkl")
receiver_geohash_weight_dict = load_object(PROJECT_PATH + "/resource_data/receiver_geohash_weight_dict.0.pkl")

# M3模型专用
supplier_id_m3_dict = load_object(PROJECT_PATH + "/resource_data/supplier_id_m3_dict.0.pkl")
receiver_geohash_m3_dict = load_object(PROJECT_PATH + "/resource_data/receiver_geohash_m3_dict.0.pkl")


def courier_feedback_poi(receiver_lng, receiver_lat):
    receiver_geohash = geohash.encode(float(receiver_lat), float(receiver_lng), 7)
    occur_num = courier_feedback_poi_dict.get(str(receiver_geohash), 0)
    is_courier_feedback_poi = 1 if occur_num >= 1 else 0

    return is_courier_feedback_poi


def get_poi_latency_difficulty(city_id, supplier_id, supplier_lng, supplier_lat,
                               receiver_lng, receiver_lat, get_difficulty_method):
    supplier_time_difficulty = 0.0
    receiver_time_difficulty = 0.0

    if get_difficulty_method == 'm1':
        # 获取延迟时效
        supplier_time_difficulty, receiver_time_difficulty = get_poi_latency_difficulty_m1(city_id,
                                                                                           supplier_id,
                                                                                           supplier_lng,
                                                                                           supplier_lat,
                                                                                           receiver_lng,
                                                                                           receiver_lat)
    elif get_difficulty_method == 'm2':
        supplier_time_difficulty, receiver_time_difficulty = get_poi_latency_difficulty_m2(supplier_id,
                                                                                           receiver_lng,
                                                                                           receiver_lat)
    elif get_difficulty_method == 'm3':
        supplier_time_difficulty, receiver_time_difficulty = get_poi_latency_difficulty_m3(city_id,
                                                                                           supplier_id,
                                                                                           receiver_lng,
                                                                                           receiver_lat)

    return supplier_time_difficulty, receiver_time_difficulty


def read_supplier_time_difficulty(city_id, supplier_id, supplier_lng,
                                  supplier_lat):
    """
    获取商户取货难度系数，优先使用cache数据
    :param city_id:
    :param supplier_id:
    :param supplier_lng:
    :param supplier_lat:
    :return:
    """
    supplier_time_difficulty = 0.0

    # 从缓存获取
    supplier_cache_key = cache_keys.SUPPLIER_TIME_DIFFICULTY.format(
        supplier_id=supplier_id, supplier_lng=supplier_lng,
        supplier_lat=supplier_lat, city_id=city_id,
    )
    supplier_time_cache = cache.get(supplier_cache_key)

    if supplier_time_cache is not None:
        supplier_time_difficulty = supplier_time_cache
    else:
        # 从数据库获取
        supplier_result = POISupplierTimeDifficulty.query \
            .filter(POISupplierTimeDifficulty.supplier_id == supplier_id,
                    POISupplierTimeDifficulty.supplier_lng == supplier_lng,
                    POISupplierTimeDifficulty.supplier_lat == supplier_lat,
                    POISupplierTimeDifficulty.city_id == city_id) \
            .first()
        if supplier_result:
            supplier_time_difficulty = supplier_result.poi_value

        cache.set(supplier_cache_key, supplier_time_difficulty,
                  cache_expire.CHCHE_EXPIRE_TIME_LONG)

    return supplier_time_difficulty


def read_poi_receiver_time_difficulty(city_id, receiver_lng, receiver_lat):
    """
    获取POI维度送达时间难度系数，优先使用缓存数据
    :param city_id:
    :param receiver_lng:
    :param receiver_lat:
    :return:
    """
    receiver_time_difficulty = 0.0

    #从缓存中获取
    receiver_cache_key = cache_keys.RECEIVER_TIME_DIFFICULTY.format(
        receiver_lng=receiver_lng, receiver_lat=receiver_lat, city_id=city_id,
    )
    receiver_time_cache = cache.get(receiver_cache_key)

    if receiver_time_cache is not None:
        receiver_time_difficulty = receiver_time_cache
    else:
        # 从数据库获取
        receiver_result = POIReceiverTimeDifficulty.query \
            .filter(POIReceiverTimeDifficulty.receiver_lng == receiver_lng,
                    POIReceiverTimeDifficulty.receiver_lat == receiver_lat,
                    POIReceiverTimeDifficulty.city_id == city_id) \
            .first()

        if receiver_result:
            receiver_time_difficulty = receiver_result.poi_value

        cache.set(receiver_cache_key, receiver_time_difficulty,
                  cache_expire.CHCHE_EXPIRE_TIME_LONG)

    return receiver_time_difficulty


def get_poi_latency_difficulty_m1(city_id, supplier_id, supplier_lng, supplier_lat, receiver_lng, receiver_lat):
    """
    获取取货难度系数，送达难度系数
    :param city_id:
    :param supplier_id:
    :param supplier_lng:
    :param supplier_lat:
    :param receiver_lng:
    :param receiver_lat:
    :return:
    """
    supplier_time_difficulty = read_supplier_time_difficulty(
        city_id=city_id,
        supplier_id=supplier_id,
        supplier_lng=supplier_lng,
        supplier_lat=supplier_lat
    )

    receiver_time_difficulty = read_poi_receiver_time_difficulty(
        city_id=city_id,
        receiver_lat=receiver_lat,
        receiver_lng=receiver_lng
    )

    return supplier_time_difficulty, receiver_time_difficulty


def get_poi_latency_difficulty_m2(supplier_id, receiver_lng, receiver_lat):
    """
    获取取货难度系数，送达难度系数
    :param supplier_id:
    :param receiver_lng:
    :param receiver_lat:
    :return:
    """
    # supplier_id_weight_dict = load_object(PROJECT_PATH + "/resource_data/supplier_id_weight_dict.0.pkl")
    # receiver_geohash_weight_dict = load_object(PROJECT_PATH + "/resource_data/receiver_geohash_weight_dict.0.pkl")

    supplier_id_weight = supplier_id_weight_dict.get(str(supplier_id), 0)
    supplier_weight_min = -4.0
    supplier_weight_max = 4.0
    supplier_time_difficulty = 1.0 - normalize(supplier_id_weight, supplier_weight_min, supplier_weight_max)

    receiver_geohash = geohash.encode(float(receiver_lat), float(receiver_lng), 7)
    receiver_geohash_weight = receiver_geohash_weight_dict.get(str(receiver_geohash), 0)
    receiver_weight_min = -4.0
    receiver_weight_max = 4.0
    receiver_time_difficulty = 1.0 - normalize(receiver_geohash_weight, receiver_weight_min, receiver_weight_max)

    return supplier_time_difficulty, receiver_time_difficulty


def get_poi_latency_difficulty_m3(city_id, supplier_id, receiver_lng, receiver_lat):
    """
    获取取货难度系数，送达难度系数
    :param city_id:
    :param supplier_id:
    :param receiver_lng:
    :param receiver_lat:
    :return:
    """
    # supplier_id_m3_dict = load_object(PROJECT_PATH + "/resource_data/supplier_id_m3_dict.0.pkl")
    # receiver_geohash_m3_dict = load_object(PROJECT_PATH + "/resource_data/receiver_geohash_m3_dict.0.pkl")
    supplier_time_difficulty = supplier_id_m3_dict.get(int(city_id), {}).get(int(supplier_id), 0)
    receiver_geohash = geohash.encode(float(receiver_lat), float(receiver_lng), 7)
    receiver_time_difficulty = receiver_geohash_m3_dict.get(int(city_id), {}).get(str(receiver_geohash), 0)

    return supplier_time_difficulty, receiver_time_difficulty


def get_poi_latency_score(alpha_1, alpha_2, supplier_time_difficulty,
                          receiver_time_difficulty):
    latency_score = 0.0

    # 计算难度系数
    latency_score = alpha_1 * supplier_time_difficulty + alpha_2 * receiver_time_difficulty

    if latency_score < 0.0:
        latency_score = 0.0
    if latency_score > 1.0:
        latency_score = 1.0

    return latency_score


def get_latency_delta(original_latency, dynamic_latency_ratio, latency_step=300, min_latency_delta=0, max_latency_delta=2400):
    dynamic_latency_delta = round((original_latency * dynamic_latency_ratio) / int(latency_step)) \
                            * int(latency_step)

    if dynamic_latency_delta <= min_latency_delta:
        dynamic_latency_delta = min_latency_delta
    elif dynamic_latency_delta >= max_latency_delta:
        dynamic_latency_delta = max_latency_delta

    return dynamic_latency_delta


if __name__ == "__main__":
    receiver_lat = 29.56418
    receiver_lng = 106.45703
    is_courier_feedback_poi = courier_feedback_poi(receiver_lng, receiver_lat)
    print "is_courier_feedback_poi: ", is_courier_feedback_poi

    pass
