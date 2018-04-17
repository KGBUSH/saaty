# -*- coding: utf-8 -*-
import datetime
from flask import request
from common.framework.views import JsonView
from core import app
from core import kafkaBizLogger
from core import sentry
from saaty.constants import kafka_event
from saaty.utils.abtest import get_order_ab_test_flag
from saaty.services.poi_time_latency import get_poi_latency_score

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

        try:
            order_id = int(request.args['orderId'])
            original_latency = int(request.args['originalLatency'])
            supplier_id = int(request.args['supplierId'])
            supplier_lng = float(request.args['supplierLng'])
            supplier_lat = float(request.args['supplierLat'])
            city_id = int(request.args['cityId'])
            receiver_lng = float(request.args['receiverLng'])
            receiver_lat = float(request.args['receiverLat'])
        except(TypeError, ValueError, KeyError):
            self.update_errors(self.error_messages['args_error'])
            return {}

        dynamic_latency_ratio = 0.0
        change_latency_success = 0
        ab_test_flag = 100
        latency_score = 0.0
        supplier_time_difficulty = 0.0
        receiver_time_difficulty = 0.0
        is_service_open = 0

        if app.config.get("POI_LATENCY_GLOBAL_SWITCH", 0):
            is_service_open = 1
            try:
                # 获取城市激活列表
                enable_city_list = app.config.get("POI_LATENCY_CITY_ENABLE_LIST", [])
                if city_id in enable_city_list:
                    # 获取AB测试分组
                    ab_test_flag = get_order_ab_test_flag(order_id, city_id)

                    # 获取延迟时效
                    latency_score, supplier_time_difficulty, receiver_time_difficulty = get_poi_latency_score(city_id,
                                                                                                              supplier_id,
                                                                                                              supplier_lng,
                                                                                                              supplier_lat,
                                                                                                              receiver_lng,
                                                                                                              receiver_lat)

                    # 获取策略分组
                    latency_schema_group = app.config.get("POI_LATENCY_SCHEMA_GROUP", {})
                    if latency_schema_group:
                        param_group = latency_schema_group[ab_test_flag]
                        if latency_score >= param_group.get("threshold", 0):
                            dynamic_latency_ratio = param_group["schema"][int(10 * latency_score)]
                            change_latency_success = 1
            except:
                sentry.captureException()
        else:
            pass

        info = {
            "is_service_open":is_service_open,
            "order_id": order_id,
            "original_latency": original_latency,
            "supplier_id": supplier_id,
            "supplier_lng": supplier_lng,
            "supplier_lat": supplier_lat,
            "city_id": city_id,
            "receiver_lng": receiver_lng,
            "receiver_lat": receiver_lat,
            "dynamic_latency_ratio": dynamic_latency_ratio,
            "ab_test_flag": ab_test_flag,
            "latency_score": latency_score,
            "supplier_time_difficulty": supplier_time_difficulty,
            "receiver_time_difficulty": receiver_time_difficulty,
            "now_timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "change_latency_success": change_latency_success
        }

        kafkaBizLogger.info(kafka_event.DYNAMIC_POI_TIME_EVENT, info)

        context = {
            'LatencyRatio': dynamic_latency_ratio,
        }

        return context
