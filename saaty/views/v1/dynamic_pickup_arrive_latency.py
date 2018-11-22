#!/usr/bin/python
#  -*- coding: utf-8 -*-
#
# Copyright (C) 2018 LIU Yiming <liuyiming@imdada.cn>
# TAPD -> https://www.tapd.cn/22169481/prong/stories/view/1122169481001001978


from flask import request
from common.framework.views import JsonView
from core import app
from core import sentry
from saaty.utils.order_category import get_vip_label, get_exclusive_label
from saaty.services.dynamic_pickup_arrive_latency_service import get_vip_assign_latency_result
from saaty.services.dynamic_pickup_arrive_latency_service import get_exclusive_assign_latency_result


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
        except(TypeError, ValueError, KeyError):
            self.update_errors(self.error_messages['args_error'])
            return {}

        # 待返回的变量
        context = {
            'pickUp': {
                'LatencyRatio': 0.0,
                'LatencyDelta': 0
            },
            'arrive': {
                'LatencyRatio': 0.0,
                'LatencyDelta': 0
            }
        }

        # 接口服务开关
        service_global_switch = app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_GLOBAL_SWITCH", 0)
        if service_global_switch:
            try:
                # 特派订单延时
                is_vip_latency_service_open = app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_VIP_ASSIGN_SWITCH", 0)
                vip_assign_flag = get_vip_label(label_ids)
                if is_vip_latency_service_open and vip_assign_flag:
                    pickup_latency_ratio, pickup_latency_delta, arrive_latency_ratio, arrive_latency_delta = \
                        get_vip_assign_latency_result(
                            city_id=city_id,
                            order_id=order_id,
                            supplier_id=supplier_id,
                            supplier_lng=supplier_lng,
                            supplier_lat=supplier_lat,
                            receiver_lng=receiver_lng,
                            receiver_lat=receiver_lat,
                            original_pickup_latency=original_pickup_latency,
                            original_arrive_latency=original_arrive_latency,
                            label_ids=label_ids
                        )
                    context = {
                        'pickUp': {
                            'LatencyRatio': pickup_latency_ratio,
                            'LatencyDelta': pickup_latency_delta
                        },
                        'arrive': {
                            'LatencyRatio': arrive_latency_ratio,
                            'LatencyDelta': arrive_latency_delta
                        }
                    }

                # 专享订单延时
                is_exclusive_latency_service_open = app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_EXCLUSIVE_ASSIGN_SWITCH", 0)
                exclusive_assign_flag = get_exclusive_label(label_ids)
                if is_exclusive_latency_service_open and exclusive_assign_flag:
                    pickup_latency_ratio, pickup_latency_delta, arrive_latency_ratio, arrive_latency_delta = \
                        get_exclusive_assign_latency_result(
                            city_id=city_id,
                            order_id=order_id,
                            supplier_id=supplier_id,
                            supplier_lng=supplier_lng,
                            supplier_lat=supplier_lat,
                            receiver_lng=receiver_lng,
                            receiver_lat=receiver_lat,
                            original_pickup_latency=original_pickup_latency,
                            original_arrive_latency=original_arrive_latency,
                            label_ids=label_ids
                        )
                    context = {
                        'pickUp': {
                            'LatencyRatio': pickup_latency_ratio,
                            'LatencyDelta': pickup_latency_delta
                        },
                        'arrive': {
                            'LatencyRatio': arrive_latency_ratio,
                            'LatencyDelta': arrive_latency_delta
                        }
                    }

            except:
                sentry.captureException()

        return context
