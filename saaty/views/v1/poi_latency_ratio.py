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
from saaty.services.poi_time_latency import get_poi_latency_score
from saaty.services.poi_time_latency import get_poi_latency_ratio
from saaty.services.poi_time_latency import get_poi_latency_delta

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
        except(TypeError, ValueError, KeyError):
            self.update_errors(self.error_messages['args_error'])
            return {}

        dynamic_latency_ratio = 0.0
        dynamic_latency_delta = 0.0
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

                    # 获取延迟时效
                    latency_score, supplier_time_difficulty, receiver_time_difficulty = get_poi_latency_score(city_id,
                                                                                                              supplier_id,
                                                                                                              supplier_lng,
                                                                                                              supplier_lat,
                                                                                                              receiver_lng,
                                                                                                              receiver_lat)

                    # ab_test_flag, dynamic_latency_ratio, change_latency_success = \
                    #     get_poi_latency_ratio(order_id, city_id, latency_score)

                    ab_test_flag, dynamic_latency_ratio, dynamic_latency_delta, change_latency_success = \
                        get_poi_latency_delta(order_id, city_id, original_latency, latency_score)
            except:
                sentry.captureException()
        else:
            pass

        end_time = time.time()

        info = {
            "is_service_open": is_service_open,
            "order_id": order_id,
            "original_latency": original_latency,
            "supplier_id": supplier_id,
            "supplier_lng": supplier_lng,
            "supplier_lat": supplier_lat,
            "city_id": city_id,
            "receiver_lng": receiver_lng,
            "receiver_lat": receiver_lat,
            "dynamic_latency_ratio": dynamic_latency_ratio,
            "dynamic_latency_delta": dynamic_latency_delta,
            "ab_test_flag": ab_test_flag,
            "latency_score": latency_score,
            "supplier_time_difficulty": supplier_time_difficulty,
            "receiver_time_difficulty": receiver_time_difficulty,
            "now_timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "change_latency_success": change_latency_success,
            "time_used": round(end_time-start_time, 3)
        }

        kafkaBizLogger.info(kafka_event.DYNAMIC_POI_TIME_EVENT, info)

        context = {
            'LatencyRatio': dynamic_latency_ratio,
            'LatencyDelta': dynamic_latency_delta,
        }

        return context
