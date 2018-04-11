# -*- coding: utf-8 -*-
import datetime
from flask import request
from common.framework.views import JsonView
from core import app
from core import kafkaBizLogger
from saaty.constants import kafka_event
from saaty.services.abtest import  get_order_ab_test_flag
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
            original_latency = int(request.args['original_latency'])
            supplier_id = int(request.args['supplierId'])
            supplier_lng = float(request.args['supplierLng'])
            supplier_lat = float(request.args['supplierLat'])
            city_id = int(request.args['cityId'])
            receiver_lng = float(request.args['receiverLng'])
            receiver_lat = float(request.args['receiverLat'])
        except(TypeError, ValueError, KeyError):
            self.update_errors(self.error_messages['args_error'])
            return {}

        # 获取AB测试分组
        ab_test_flag = get_order_ab_test_flag(order_id, city_id)

        # 获取延迟时效
        dynamic_latency_ratio = get_poi_latency_score(city_id, supplier_id, \
                                                      supplier_lng, supplier_lat, receiver_lng, receiver_lat)

        info = {
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
            "now_timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        kafkaBizLogger.info(kafka_event.DYNAMIC_POI_TIME_EVENT, info)

        context = {
            'poi_latency_ratio': dynamic_latency_ratio,
        }
        return context

