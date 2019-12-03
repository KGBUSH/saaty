# -*- coding: utf-8 -*-


import json
import pandas as pd
import time
from flask import request
from core import sentry, app
from common.framework.views import JsonView
from saaty.services.eta_service import get_eta_a_overhead_v2
from saaty.services.eta_service import get_eta_a_batch_overhead

__all__ = [
    'EtaAOverHeadView',
    'EtaABatchOverHeadView'
]


class EtaAOverHeadView(JsonView):
    methods = ['POST', ]

    decorators = []

    error_messages = {
        'args_error': u'参数错误',
    }

    def post(self, **kwargs):
        try:
            data = json.loads(request.data)
            transporter_id = int(data['transporterId'])
            transporter_lat = float(data['transporterLat'])
            transporter_lng = float(data['transporterLng'])
            supplier_id = int(data['supplierId'])
            supplier_lat = float(data['supplierLat'])
            supplier_lng = float(data['supplierLng'])
            timestamp = int(data['timestamp'])
            city_id = int(data['cityId'])
            cargo_type_id = int(data['cargoTypeID'])
            cargo_weight = float(data['cargoWeight'])
        except Exception:
            sentry.captureException()
            self.update_errors(self.error_messages['args_error'])
            return self.render_to_response()

        hour = pd.Timestamp(timestamp, unit='s', tz='Asia/Shanghai').hour
        weekday = pd.Timestamp(timestamp, unit='s', tz='Asia/Shanghai').dayofweek
        [status, pred_a1, pred_a2] = get_eta_a_overhead_v2(transporter_id, transporter_lat, transporter_lng,
                                                           supplier_id, supplier_lat, supplier_lng,
                                                           hour, city_id, weekday,
                                                           cargo_type_id, cargo_weight)
        context = {
            'etaStatus': status,
            'acceptToArriveSeconds': pred_a1,
            'arriveToFetchSeconds': pred_a2
        }

        return self.render_to_response(context)


class EtaABatchOverHeadView(JsonView):
    methods = ['POST', ]

    decorators = []

    error_messages = {
        'args_error': u'参数错误',
    }

    def post(self, **kwargs):
        data_list = []
        try:
            data = json.loads(request.data)
            content = data['orderList']
            if isinstance(content, list) and len(content) > 0:
                for i in range(len(content)):
                    transporter_id = int(content[i]['transporterId'])
                    transporter_lat = float(content[i]['transporterLat'])
                    transporter_lng = float(content[i]['transporterLng'])
                    supplier_id = int(content[i]['supplierId'])
                    supplier_lat = float(content[i]['supplierLat'])
                    supplier_lng = float(content[i]['supplierLng'])
                    city_id = int(content[i]['cityId'])
                    timestamp = int(content[i]['timestamp'])
                    cargo_type_id = int(content[i]['cargoTypeID'])
                    cargo_weight = float(content[i]['cargoWeight'])
                    hour = pd.Timestamp(timestamp, unit='s', tz='Asia/Shanghai').hour
                    weekday = pd.Timestamp(timestamp, unit='s', tz='Asia/Shanghai').dayofweek

                    data_list.append({'transporter_id': transporter_id,
                                      'transporter_lat': transporter_lat,
                                      'transporter_lng': transporter_lng,
                                      'supplier_id': supplier_id,
                                      'supplier_lat': supplier_lat,
                                      'supplier_lng': supplier_lng,
                                      'hour': hour,
                                      'city_id': city_id,
                                      'weekday': weekday,
                                      'cargo_type_id': cargo_type_id,
                                      'cargo_weight': cargo_weight
                                      }
                                     )
        except (KeyError, TypeError, ValueError):
            sentry.captureException()
            self.update_errors(self.error_messages['args_error'])
            return self.render_to_response()

        res_eta_list = get_eta_a_batch_overhead(order_list=data_list)

        context = {
            'predictions': [
                {'etaStatus': res_info[0],
                 'acceptToArriveSeconds': res_info[1],
                 'arriveToFetchSeconds': res_info[2]}
                for res_info in res_eta_list
            ]
        }
        return self.render_to_response(context)
