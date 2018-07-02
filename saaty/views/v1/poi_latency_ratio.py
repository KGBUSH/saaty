# -*- coding: utf-8 -*-
import datetime
import time
from flask import request
from common.framework.views import JsonView
from core import app
from core import kafkaBizLogger
from core import sentry
from saaty.constants import kafka_event
from saaty.utils.abtest import get_order_ab_test_flag
from saaty.utils.config_detail import get_config_detail
from saaty.utils.order_category import get_order_category
from saaty.services.poi_time_latency import get_poi_latency_difficulty
from saaty.services.poi_time_latency import get_poi_latency_score
from saaty.services.poi_time_latency import get_latency_delta
from saaty.services.poi_time_latency import courier_feedback_poi


__all__ = [
    'POILatencyRatioView',
]


class POILatencyRatioView(JsonView):
    """
    This is poi rank view.
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
            original_latency = int(request.args['originalLatency'])
            supplier_id = int(request.args['supplierId'])
            supplier_lng = str(request.args['supplierLng'])
            supplier_lat = str(request.args['supplierLat'])
            city_id = int(request.args['cityId'])
            receiver_lng = str(request.args['receiverLng'])
            receiver_lat = str(request.args['receiverLat'])
            label_ids = str(request.args['lableIDs'])
        except(TypeError, ValueError, KeyError):
            self.update_errors(self.error_messages['args_error'])
            return {}

        # 初始化
        dynamic_latency_ratio = 0.0
        dynamic_latency_delta = 0.0
        is_latency_changed = 0
        ab_test_flag = 'con_101_m1'
        control_flag = 1
        latency_config_group = 101
        param_group = {
            'schema': [0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.3, 0.4],
            'threshold': 0.7,
            'alpha_1': 0.5,
            'alpha_2': 0.5
        }
        latency_score = 0.0
        get_difficulty_method = 'm1'
        is_courier_feedback_poi = 0
        supplier_time_difficulty = 0.0
        receiver_time_difficulty = 0.0
        is_service_open = 0

        order_category = get_order_category(label_ids)

        if app.config.get("POI_LATENCY_GLOBAL_SWITCH", 0):
            is_service_open = 1
            try:
                # 获取城市激活列表
                enable_city_list = app.config.get("POI_LATENCY_CITY_ENABLE_LIST", [])

                if city_id in enable_city_list:
                    # 获取AB测试分组
                    city_group = 'POI_LATENCY_CITY_AB_TEST'
                    test_name = 'saaty_order'
                    ab_test_flag = get_order_ab_test_flag(order_id, city_id, city_group, test_name)

                    control_flag, latency_config_group, get_difficulty_method = get_config_detail(ab_test_flag)

                    # 骑士反馈的问题poi直接进行延时
                    is_courier_feedback_poi = courier_feedback_poi(receiver_lng, receiver_lat)
                    if is_courier_feedback_poi:
                        dynamic_latency_ratio = app.config.get("POI_LATENCY_RATIO_COURIER_FEEDBACK", 0.3)
                        is_latency_changed = 1
                    else:
                        supplier_time_difficulty, receiver_time_difficulty = get_poi_latency_difficulty(city_id,
                                                                                                        supplier_id,
                                                                                                        supplier_lng,
                                                                                                        supplier_lat,
                                                                                                        receiver_lng,
                                                                                                        receiver_lat,
                                                                                                        get_difficulty_method)

                        # 获取策略分组
                        latency_schema_group = app.config.get("POI_LATENCY_SCHEMA_GROUP", {})
                        param_group = latency_schema_group.get(latency_config_group, {})

                        alpha_1 = param_group.get("alpha_1", 0.5)
                        alpha_2 = param_group.get("alpha_2", 0.5)
                        latency_score = get_poi_latency_score(alpha_1,
                                                              alpha_2,
                                                              supplier_time_difficulty,
                                                              receiver_time_difficulty)

                        if latency_schema_group:
                            if latency_score >= param_group.get("threshold", 0):
                                dynamic_latency_ratio = param_group["schema"][int(10 * latency_score)]
                                is_latency_changed = 1

                    # 将比例转化为固定的时间延迟
                    latency_step = 300
                    min_latency_delta = 0
                    max_latency_delta = app.config.get("POI_LATENCY_MAX_LATENCY_DELTA", 2400)
                    dynamic_latency_delta = get_latency_delta(original_latency,
                                                              dynamic_latency_ratio,
                                                              latency_step,
                                                              min_latency_delta,
                                                              max_latency_delta)
            except:
                sentry.captureException()
        else:
            pass

        end_time = time.time()

        info = {
            "is_service_open": is_service_open,
            "order_id": order_id,
            "label_ids": label_ids,
            "order_category": order_category,
            "city_id": city_id,
            "original_latency": original_latency,
            "supplier_id": supplier_id,
            "supplier_lng": supplier_lng,
            "supplier_lat": supplier_lat,
            "receiver_lng": receiver_lng,
            "receiver_lat": receiver_lat,
            "dynamic_latency_ratio": dynamic_latency_ratio,
            "dynamic_latency_delta": dynamic_latency_delta,
            "ab_test_flag": ab_test_flag,
            "control_flag": control_flag,
            "latency_config_group": latency_config_group,
            "param_group": param_group,
            "get_difficulty_method": get_difficulty_method,
            "is_courier_feedback_poi": is_courier_feedback_poi,
            "latency_score": latency_score,
            "supplier_time_difficulty": supplier_time_difficulty,
            "receiver_time_difficulty": receiver_time_difficulty,
            "now_timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "is_latency_changed": is_latency_changed,
            "time_used": round(end_time-start_time, 3)
        }

        kafkaBizLogger.info(kafka_event.DYNAMIC_POI_TIME_EVENT, info)

        if 1 == control_flag:
            dynamic_latency_ratio = 0.0
            dynamic_latency_delta = 0

        mode_switch_test = app.config.get("TEST_MODE_SWITCH", 0)
        if mode_switch_test:
            dynamic_latency_ratio = app.config.get("TEST_DYNAMIC_LATENCY_RATIO", 0.0)
            dynamic_latency_delta = app.config.get("TEST_DYNAMIC_LATENCY_DELTA", 0)

        context = {
            'LatencyRatio': dynamic_latency_ratio,
            'LatencyDelta': dynamic_latency_delta,
        }

        return context
