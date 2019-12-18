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
from saaty.services.eta_service import get_eta_c_overhead

__all__ = [
    'EtaCOverHeadView',
    # 'EtaABatchOverHeadView'
]


class EtaCOverHeadView(JsonView):
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

            receiver_address = data['receiverAddress']
            receiver_lat = float(data['receiverLat'])
            receiver_lng = float(data['receiverLng'])

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
        [status, pred_c] = get_eta_c_overhead(transporter_id, receiver_address, receiver_lat, receiver_lng,
                                                        hour, city_id, weekday,
                                                        cargo_type_id, cargo_weight)
        context = {
            'etaStatus': status,
            'deliverySeconds': pred_c,
        }

        end_time = time.time()
        info = {
            "transporter_id": transporter_id,
            "receiver_address": receiver_address,
            "receiver_lat": receiver_lat,
            "receiver_lng": receiver_lng,
            "timestamp": timestamp,
            "city_id": city_id,
            "cargo_type_id": cargo_type_id,
            "cargo_weight": cargo_weight,
            "hour": hour,

            "now_timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "time_used": round(end_time - start_time, 3),

            "status": status,
            "pred_c": pred_c,
        }
        algoKafkaLogger.info(kafka_event.ETA_DELIVERY_EVENT, info)

        return self.render_to_response(context)
