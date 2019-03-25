# -*- coding: utf-8 -*-

from flask import request
from common.framework.views import JsonView
from core import app
import saaty.services.poi_time_latency as poi_latency_service
from core import algoKafkaLogger
from saaty.constants import kafka_event


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
            order_id = int(request.args.get('orderId', 0))  # 不必需
            original_latency = int(request.args.get('originalLatency', 0))  # 单位：s，不必需
            supplier_id = int(request.args['supplierId'])
            supplier_lng = str(request.args['supplierLng'])
            supplier_lat = str(request.args['supplierLat'])
            city_id = int(request.args['cityId'])
            receiver_lng = str(request.args['receiverLng'])
            receiver_lat = str(request.args['receiverLat'])
            label_ids = str(request.args['lableIDs'])
            # 运营在雨天会有额外的延时配置
            heavy_weather_latency = int(request.args.get('heavyWeatherTime', 0))*60  # 单位：s，不必需
        except(TypeError, ValueError, KeyError):
            self.update_errors(self.error_messages['args_error'])
            return {}

        # 待返回的变量初始化
        context = {
            'LatencyRatio': 0.0,
            'LatencyDelta': 0,
        }

        # 困难POI延时
        if app.config.get("POI_LATENCY_GLOBAL_SWITCH", 0):
            dynamic_latency_ratio, dynamic_latency_delta = poi_latency_service.get_poi_latency_view_result(
                city_id=city_id,
                supplier_id=supplier_id,
                supplier_lat=supplier_lat,
                supplier_lng=supplier_lng,
                receiver_lat=receiver_lat,
                receiver_lng=receiver_lng,
                original_latency=original_latency,
                order_id=order_id,
                label_ids=label_ids,
                heavy_weather_latency=heavy_weather_latency
            )
            context = {
                'LatencyRatio': dynamic_latency_ratio,
                'LatencyDelta': dynamic_latency_delta,
            }

        # 指定区域延时开关
        if app.config.get("SPECIFIC_BLOCK_LATENCY_SWITCH", 0):
            is_specific_block_latency, latency_delta = poi_latency_service.is_specific_block_latency_dealing(
                city_id=city_id,
                supplier_lat=supplier_lat,
                supplier_lng=supplier_lng,
                receiver_lat=receiver_lat,
                receiver_lng=receiver_lng,
                order_id=order_id
            )
            if is_specific_block_latency:
                context = {
                    'LatencyRatio': round(float(latency_delta)/original_latency, 2) if original_latency > 0 else 0.0,
                    'LatencyDelta': app.config.get("SPECIFIC_BLOCK_LATENCY_TIME", 600)
                }

        # 接口响应日志
        request_respons_info = {
            "order_id": order_id,
            "original_latency": original_latency,
            "supplier_id": supplier_id,
            "supplier_lng": supplier_lng,
            "supplier_lat": supplier_lat,
            "city_id": city_id,
            "receiver_lng": receiver_lng,
            "receiver_lat": receiver_lat,
            "label_ids": label_ids,
            "heavy_weather_latency": heavy_weather_latency,
            "response_context": context
        }
        algoKafkaLogger.info(kafka_event.DYNAMIC_POI_LATENCY_ONLINE_CHECK, request_respons_info)

        return context
