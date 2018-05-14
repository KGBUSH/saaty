#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 xuekun.zhuang <zhuangxuekun@imdada.cn>
from core import app
from saaty.models.poi_time_difficulty import POIReceiverTimeDifficulty
from saaty.models.poi_time_difficulty import POISupplierTimeDifficulty


def get_poi_latency_difficulty(city_id, supplier_id, supplier_lng, supplier_lat, receiver_lng, receiver_lat):
    supplier_time_difficulty = 0.0
    receiver_time_difficulty = 0.0

    # 获取取货成本难度系数
    supplier_result = POISupplierTimeDifficulty.query \
        .filter(POISupplierTimeDifficulty.supplier_id == supplier_id,
                POISupplierTimeDifficulty.supplier_lng == supplier_lng,
                POISupplierTimeDifficulty.supplier_lat == supplier_lat,
                POISupplierTimeDifficulty.city_id == city_id) \
        .first()
    if supplier_result:
        supplier_time_difficulty = supplier_result.poi_value

    # 获取送达成本难度系数
    receiver_result = POIReceiverTimeDifficulty.query \
        .filter(POIReceiverTimeDifficulty.receiver_lng == receiver_lng,
                POIReceiverTimeDifficulty.receiver_lat == receiver_lat,
                POIReceiverTimeDifficulty.city_id == city_id) \
        .first()

    if receiver_result:
        receiver_time_difficulty = receiver_result.poi_value

    return supplier_time_difficulty, receiver_time_difficulty


def get_poi_latency_score(alpha_1, alpha_2, supplier_time_difficulty, receiver_time_difficulty):
    latency_score = 0.0

    # 计算难度系数
    latency_score = alpha_1 * supplier_time_difficulty + alpha_2 * receiver_time_difficulty

    return latency_score


def get_poi_latency_delta(original_latency, dynamic_latency_ratio):
    min_latency_delta = 0
    # 延时上限=40min
    max_latency_delta = app.config.get("POI_LATENCY_MAX_LATENCY_DELTA", 2400)
    dynamic_latency_delta = round((original_latency * dynamic_latency_ratio) / 300) * 300

    if dynamic_latency_delta <= min_latency_delta:
        dynamic_latency_delta = min_latency_delta
    elif dynamic_latency_delta >= max_latency_delta:
        dynamic_latency_delta = max_latency_delta

    return dynamic_latency_delta
