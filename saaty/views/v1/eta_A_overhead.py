# -*- coding: utf-8 -*-

import datetime
import json
import pandas as pd
import time
from flask import request
from core import sentry, app
from core import kafkaBizLogger
from core import algoKafkaLogger
from common.framework.views import JsonView
from saaty.constants import kafka_event
from saaty.services.eta_service import get_eta_a_overhead_v2
from saaty.services.eta_service import get_eta_a_batch_overhead, get_eta_a_overhead_v2_batch

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
        start_time = time.time()
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
        except (KeyError, TypeError, ValueError):
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

        end_time = time.time()
        info = {
            "transporter_id": transporter_id,
            "transporter_lat": transporter_lat,
            "transporter_lng": transporter_lng,
            "supplier_id": supplier_id,
            "supplier_lat": supplier_lat,
            "supplier_lng": supplier_lng,
            "weekday": weekday,
            "timestamp": timestamp,
            "hour": hour,
            "cargo_type_id": cargo_type_id,
            "cargo_weight": cargo_weight,

            "now_timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "time_used": round(end_time - start_time, 3),
            "city_id": city_id,

            "status": status,
            "pred_a1": pred_a1,
            "pred_a2": pred_a2,
        }
        algoKafkaLogger.info(kafka_event.ETA_ACCEPT_TO_ARRIVE_TOFETCH_EVENT, info)

        return self.render_to_response(context)


class EtaABatchOverHeadView(JsonView):
    methods = ['POST', ]

    decorators = []

    error_messages = {
        'args_error': u'参数错误',
    }

    def post(self, **kwargs):
        start_time = time.time()
        data_list = []
        try:
            data = json.loads(request.data)
            request_id = data.get('requestId', '')
            content = data['orderList']
            if isinstance(content, list) and len(content) > 0:
                for i in range(len(content)):
                    order_id = int(content[i]['orderId'])
                    transporter_id = int(content[i]['transporterId'])
                    transporter_lat = float(content[i]['transporterLat'])
                    transporter_lng = float(content[i]['transporterLng'])
                    supplier_id = int(content[i]['supplierId'])
                    supplier_lat = float(content[i]['supplierLat'])
                    supplier_lng = float(content[i]['supplierLng'])
                    city_id = int(content[i]['cityId'])
                    # timestamp = int(content[i]['timestamp'])
                    timestamp = start_time
                    cargo_type_id = int(content[i]['cargoTypeID'])
                    cargo_weight = float(content[i]['cargoWeight'])
                    hour = pd.Timestamp(timestamp, unit='s', tz='Asia/Shanghai').hour
                    weekday = pd.Timestamp(timestamp, unit='s', tz='Asia/Shanghai').dayofweek

                    data_list.append({
                        'order_id': order_id,
                        'transporter_id': transporter_id,
                        'transporter_lat': transporter_lat,
                        'transporter_lng': transporter_lng,
                        'supplier_id': supplier_id,
                        'supplier_lat': supplier_lat,
                        'supplier_lng': supplier_lng,
                        'timestamp': timestamp,
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

        # res_eta_list = get_eta_a_batch_overhead(order_list=data_list)
        res_eta_list = get_eta_a_overhead_v2_batch(search_list=data_list)

        context = {
            'predictions': [
                {'etaStatus': res_info[0],
                 'acceptToArriveSeconds': res_info[1],
                 'arriveToFetchSeconds': res_info[2]}
                for res_info in res_eta_list
            ]
        }

        time_used = round(time.time() - start_time, 3)
        now_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if request_id:
            for input_data, res_info in zip(data_list, res_eta_list):
                info = {}
                info.update(input_data)
                info.update({
                    'request_id': request_id,

                    'eta_status': res_info[0],
                    'accept_to_arrive_seconds': res_info[1],
                    'arrive_to_fetch_seconds': res_info[2],

                    "now_timestamp": now_timestamp,
                    "time_used": time_used,
                })
                algoKafkaLogger.info(kafka_event.ETA_ACCEPT_TO_ARRIVE_TOFETCH_EVENT, info)

        return self.render_to_response(context)
