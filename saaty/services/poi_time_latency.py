#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 xuekun.zhuang <zhuangxuekun@imdada.cn>
from core import app
from saaty.models.poi_time_difficulty import POIReceiverTimeDifficulty
from saaty.models.poi_time_difficulty import POISupplierTimeDifficulty
from saaty.utils.abtest import get_order_ab_test_flag


def get_poi_latency_score(city_id, supplier_id, supplier_lng, supplier_lat, receiver_lng, receiver_lat):
    latency_score = 0.0
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

    # 计算难度系数
    latency_param = app.config.get("POI_LATENCY_PARAM", {})
    if latency_param:
        latency_score = latency_param["alpha_1"]*supplier_time_difficulty + latency_param["alpha_2"]*receiver_time_difficulty

    return latency_score, supplier_time_difficulty, receiver_time_difficulty


def get_poi_latency_ratio(order_id, city_id, latency_score):
    ab_test_flag = 100
    dynamic_latency_ratio = 0.0
    change_latency_success = 0.0

    # 获取AB测试分组
    ab_test_flag = get_order_ab_test_flag(order_id, city_id)

    # 获取策略分组
    latency_schema_group = app.config.get("POI_LATENCY_SCHEMA_GROUP", {})
    if latency_schema_group:
        param_group = latency_schema_group[ab_test_flag]
        if latency_score >= param_group.get("threshold", 0):
            dynamic_latency_ratio = param_group["schema"][int(10 * latency_score)]
            change_latency_success = 1

    return ab_test_flag, dynamic_latency_ratio, change_latency_success


def get_poi_latency_delta(order_id, city_id, original_latency, latency_score):
    ab_test_flag = 100
    dynamic_latency_delta = 0.0
    change_latency_success = 0.0

    # 获取AB测试分组
    ab_test_flag = get_order_ab_test_flag(order_id, city_id)

    # 获取策略分组
    latency_schema_group = app.config.get("POI_LATENCY_SCHEMA_GROUP", {})
    if latency_schema_group:
        param_group = latency_schema_group[ab_test_flag]
        if latency_score >= param_group.get("threshold", 0):
            dynamic_latency_ratio = param_group["schema"][int(10 * latency_score)]
            change_latency_success = 1

    min_latency_delta = 0
    max_latency_delta = 2400  # 延时上限10min
    dynamic_latency_delta = round((original_latency * dynamic_latency_ratio) / 300) * 300
    print 'original_latency', original_latency
    print 'dynamic_latency_ratio', dynamic_latency_ratio
    print 'dynamic_latency_delta', dynamic_latency_delta
    if dynamic_latency_delta <= min_latency_delta:
        dynamic_latency_delta = min_latency_delta
    elif dynamic_latency_delta >= max_latency_delta:
        dynamic_latency_delta = max_latency_delta

    return ab_test_flag, dynamic_latency_ratio, dynamic_latency_delta, change_latency_success

