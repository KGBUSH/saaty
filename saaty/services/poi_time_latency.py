#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 xuekun.zhuang <zhuangxuekun@imdada.cn>
from core import app
from saaty.models.poi_time_difficulty import POIReceiverTimeDifficulty
from saaty.models.poi_time_difficulty import POISupplierTimeDifficulty


def get_poi_latency_score(city_id, supplier_id, supplier_lng, supplier_lat, receiver_lng, receiver_lat):
    latency_score = 0.0
    supplier_time_difficulty = 0.0
    receiver_time_difficulty = 0.0

    # 获取取货成本难度系数
    supplier_result = POISupplierTimeDifficulty.query \
        .filter(POISupplierTimeDifficulty.supplier_id == supplier_id,
                POISupplierTimeDifficulty.supplier_lng == supplier_lng,
                POISupplierTimeDifficulty.supplier_lat == supplier_lat) \
        .all()
    if supplier_result:
        supplier_time_difficulty = supplier_result[0].poi_value

    # 获取送达成本难度系数
    receiver_result = POIReceiverTimeDifficulty.query \
        .filter(POIReceiverTimeDifficulty.receiver_lng == receiver_lng,
                POIReceiverTimeDifficulty.receiver_lat == receiver_lat) \
        .all()
    if receiver_result:
        receiver_time_difficulty = receiver_result[0].poi_value

    # 计算难度系数
    latency_param = app.config.get("POI_LATENCY_PARAM", {})
    if latency_param:
        latency_score = latency_param["alpha_1"]*supplier_time_difficulty + latency_param["alpha_2"]*receiver_time_difficulty

    return latency_score, supplier_time_difficulty, receiver_time_difficulty


def get_poi_latency_ratio(latency_score):
    pass

