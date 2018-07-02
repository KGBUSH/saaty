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
from saaty.services.poi_time_latency import get_poi_latency_difficulty
from saaty.services.poi_time_latency import get_latency_delta


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
            label_ids = str(request.args['labelIDs'])
            is_vip_assign = int(request.args['isVipAssign'])
        except(TypeError, ValueError, KeyError):
            self.update_errors(self.error_messages['args_error'])
            return {}

        # 中间变量初始化
        supplier_time_difficulty = 0.0
        receiver_time_difficulty = 0.0
        is_vip_latency_service_open = 0
        ab_test_flag = 'con_100_100_m1'
        control_flag = 1
        pickup_latency_config_group = 100
        arrive_latency_config_group = 100
        pickup_param_group = {
            'schema': [0, 0, 0, 0, 0, 0, 0.1, 0.1, 0.1, 0.1],
            'threshold': 0.7
        }
        arrive_param_group = {
            'schema': [0, 0, 0, 0, 0, 0, 0.1, 0.1, 0.1, 0.1],
            'threshold': 0.7
        }
        get_difficulty_method = 'm1'

        # 待返回变量初始化
        is_pickup_latency_changed = 0
        is_arrive_latency_changed = 0
        dynamic_pickup_latency_ratio = 0.0
        dynamic_pickup_latency_delta = 0
        dynamic_arrive_latency_ratio = 0.0
        dynamic_arrive_latency_delta = 0

        order_category = get_order_category(label_ids)

        if app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_GLOBAL_SWITCH", 0):
            is_vip_latency_service_open = 1
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

                    supplier_time_difficulty, receiver_time_difficulty = get_poi_latency_difficulty(city_id,
                                                                                                    supplier_id,
                                                                                                    supplier_lng,
                                                                                                    supplier_lat,
                                                                                                    receiver_lng,
                                                                                                    receiver_lat,
                                                                                                    get_difficulty_method)

                    # 获取到店时效、送达时效策略分组
                    latency_schema_group = app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_SCHEMA_GROUP", {})
                    pickup_param_group = latency_schema_group.get(pickup_latency_config_group, {})
                    arrive_param_group = latency_schema_group.get(arrive_latency_config_group, {})

                    if latency_schema_group:
                        if supplier_time_difficulty >= pickup_param_group.get("threshold", 0):
                            dynamic_pickup_latency_ratio = pickup_param_group["schema"][int(10 * supplier_time_difficulty)]
                            is_pickup_latency_changed = 1

                        dynamic_arrive_latency_ratio = 0.0
                        is_arrive_latency_changed = 0

                    # 将比例转化为固定的时间延迟
                    latency_step = 300
                    min_pickup_latency_delta = app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_MIN_LATENCY_DELTA", 300)
                    max_pickup_latency_delta = min(app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_MAX_LATENCY_DELTA", 1200),
                                                   original_arrive_latency - original_pickup_latency)
                    if max_pickup_latency_delta > min_pickup_latency_delta:
                        dynamic_pickup_latency_delta = get_latency_delta(original_pickup_latency,
                                                                         dynamic_pickup_latency_ratio,
                                                                         latency_step,
                                                                         min_pickup_latency_delta,
                                                                         max_pickup_latency_delta)
                    else:
                        dynamic_pickup_latency_delta = 0

                    dynamic_arrive_latency_delta = 0
            except:
                sentry.captureException()

        end_time = time.time()

        info = {
            "is_vip_assign": is_vip_assign,
            "is_vip_latency_service_open": is_vip_latency_service_open,
            "order_id": order_id,
            "label_ids": label_ids,
            "order_category": order_category,
            "city_id": city_id,
            "original_pickup_latency": original_pickup_latency,
            "original_arrive_latency": original_arrive_latency,
            "supplier_id": supplier_id,
            "supplier_lng": supplier_lng,
            "supplier_lat": supplier_lat,
            "receiver_lng": receiver_lng,
            "receiver_lat": receiver_lat,
            "dynamic_pickup_latency_ratio": dynamic_arrive_latency_ratio,
            "dynamic_arrive_latency_ratio": dynamic_arrive_latency_ratio,
            "dynamic_pickup_latency_delta": dynamic_pickup_latency_delta,
            "dynamic_arrive_latency_delta": dynamic_arrive_latency_delta,
            "ab_test_flag": ab_test_flag,
            "control_flag": control_flag,
            "pickup_latency_config_group": pickup_latency_config_group,
            "arrive_latency_config_group": arrive_latency_config_group,
            "pickup_param_group": pickup_param_group,
            "arrive_param_group": arrive_param_group,
            "get_difficulty_method": get_difficulty_method,
            "supplier_time_difficulty": supplier_time_difficulty,
            "receiver_time_difficulty": receiver_time_difficulty,
            "now_timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "is_pickup_latency_changed": is_pickup_latency_changed,
            "is_arrive_latency_changed": is_arrive_latency_changed,
            "time_used": round(end_time - start_time, 3)
        }

        kafkaBizLogger.info(kafka_event.DYNAMIC_POI_TIME_EVENT, info)

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
