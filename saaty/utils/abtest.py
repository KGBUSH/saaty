#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 xuekun.zhuang <zhuangxuekun@imdada.cn>
from core import app


__all__ = [
    'get_abtest_id',
    'get_order_ab_test_flag'
]


def get_order_ab_test_flag(order_id, city_id):
    # 所有城市的ab分组流量配置
    poi_city_param = app.config.get('POI_LATENCY_CITY_AB_TEST', {})
    city_param = poi_city_param.get(city_id, {})

    abtest_flag = get_abtest_id(
        map_id=order_id,
        exp_conf=city_param,
        test_name='saaty_order'
    )

    if abtest_flag == 0:
        abtest_flag = 'None'

    return abtest_flag


def get_abtest_id(map_id, exp_conf, exp_whitelist=None, test_name='', default=0):
    abtest_id = default
    if exp_whitelist is None:
        exp_whitelist = {}
    try:
        hash_value = hash_map(test_name + str(map_id) + test_name) % 100
        if sum(exp_conf.values()) != 100:
            return abtest_id
        sum_val = 0
        for (key, value) in exp_conf.items():
            sum_val += value
            if hash_value < sum_val:
                abtest_id = key
                break
        for key, value in exp_whitelist.items():
            if map_id in value:
                abtest_id = key
    except:
        pass
    return abtest_id


def hash_map(string):
    '''
    BKDR哈希函数
    '''
    seed = 131
    hash_val = 0
    for char in string:
        hash_val = (hash_val * seed) + ord(char)
    return hash_val