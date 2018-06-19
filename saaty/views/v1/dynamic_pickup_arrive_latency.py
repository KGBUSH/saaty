#!/usr/bin/python
#  -*- coding: utf-8 -*-
#
# Copyright (C) 2018 LIU Yiming <liuyiming@imdada.cn>
# TAPD-> https://www.tapd.cn/22169481/prong/stories/view/1122169481001001978


import datetime
import time
from flask import request
from common.framework.views import JsonView
from core import app
from core import kafkaBizLogger
from core import sentry
from saaty.constants import kafka_event
from saaty.utils.abtest import get_order_ab_test_flag
from saaty.utils.config_detail import get_dynamic_pickup_arrive_config_detail
from saaty.utils.order_category import get_order_category
from saaty.services.poi_time_latency import get_poi_latency_difficulty_m1
from saaty.services.poi_time_latency import get_poi_latency_difficulty_m2
from saaty.services.poi_time_latency import get_poi_latency_difficulty_m3
from saaty.services.poi_time_latency import get_poi_latency_delta


__all__ = [
    'DynamicPickupArriveLatencyView',
]


class DynamicPickupArriveLatencyView(JsonView):
    """
        This is dynamic pickup and arrive latency view.
    """
    error_messages = {
        'args_error': u'input args error!',
    }

    methods = ['GET', ]

    decorators = []

    def get_context_data(self, **kwargs):
        start_time = time.time()

        try:
            order_id = int(request.args['orderId'])
            supplier_id = int(request.args['supplierId'])
            supplier_lng = str(request.args['supplierLng'])
            supplier_lat = str(request.args['supplierLat'])
            city_id = int(request.args['cityId'])
            receiver_lng = str(request.args['receiverLng'])
            receiver_lat = str(request.args['receiverLat'])
            original_pickup_latency = int(request.args['originalPickUpLatency'])
            original_arrive_latency = int(request.args['originalLatency'])
            # transporter_id = int(request.args['transporterId'])
            is_vip_assign = int(request.args['isVipAssign'])
        except(TypeError, ValueError, KeyError):
            self.update_errors(self.error_messages['args_error'])
            return {}

        # 中间变量初始化
        supplier_time_difficulty = 0.0
        receiver_time_difficulty = 0.0
        is_service_open = 0
        ab_test_flag = 'con_101_m1'
        control_flag = 1
        latency_config_group = 101
        param_group = {
            'schema': [0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.3, 0.4],
            'threshold': 0.7
        }
        latency_score = 0.0
        get_difficulty_method = 'm1'

        # 待返回变量初始化
        is_pickup_latency_changed = 1
        is_arrive_latency_changed = 1
        dynamic_pickup_latency_ratio = 0.0
        dynamic_pickup_latency_delta = 0.0
        dynamic_arrive_latency_ratio = 0.0
        dynamic_arrive_latency_delta = 0.0

        if app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_GLOBAL_SWITCH", 0):
            is_service_open = 1
            try:
                # 获取城市激活列表
                enable_city_list = app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_CITY_ENABLE_LIST", [])

                if 1 == is_vip_assign and city_id in enable_city_list:
                    # 获取AB测试分组
                    city_group = 'DYNAMIC_PICKUP_ARRIVE_LATENCY_CITY_AB_TEST'
                    test_name = 'dynamic_pickup_arrive'
                    ab_test_flag = get_order_ab_test_flag(order_id, city_id, city_group, test_name)

                    control_flag, pickup_latency_config_group, arrive_latency_config_group, get_difficulty_method = \
                        get_dynamic_pickup_arrive_config_detail(ab_test_flag)

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
                    # 获取到店时效、送达时效策略分组
                    latency_schema_group = app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_SCHEMA_GROUP", {})
                    pickup_param_group = latency_schema_group.get(pickup_latency_config_group, {})
                    arrive_param_group = latency_schema_group.get(arrive_latency_config_group, {})

                    if latency_schema_group:
                        if supplier_time_difficulty >= pickup_param_group.get("threshold", 0):
                            dynamic_pickup_latency_ratio = pickup_param_group["schema"][int(10 * supplier_time_difficulty)]
                            is_pickup_latency_changed = 1

                        if receiver_time_difficulty >= arrive_param_group.get("threshold", 0):
                            dynamic_arrive_latency_ratio = arrive_param_group["schema"][int(10 * receiver_time_difficulty)]
                            is_arrive_latency_changed = 1

                    # 将比例转化为固定的时间延迟
                    dynamic_pickup_latency_delta = get_poi_latency_delta(original_pickup_latency, dynamic_pickup_latency_ratio)
                    dynamic_arrive_latency_delta = get_poi_latency_delta(original_arrive_latency, dynamic_arrive_latency_ratio)

            except:
                sentry.captureException()

        context = {
            'pickUp': {
                'LatencyRatio': dynamic_pickup_latency_ratio,
                'LatencyDelta': dynamic_pickup_latency_delta
            },
            'arrive': {
                'LatencyRatio': dynamic_arrive_latency_ratio,
                'LatencyDelta': dynamic_arrive_latency_delta
            }
        }

        return context
