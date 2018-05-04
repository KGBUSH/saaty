# -*- coding: utf-8 -*-
import datetime
import time
from common.framework.views import JsonFormView
from core import app
from core import sentry
from core import kafkaBizLogger
from saaty.constants import kafka_event
from saaty.forms.poi_time_value_form import ReceiverTimeForm
from saaty.services.poi_time_value_service import \
    get_receiver_time_overhead_value_list

__all__ = [
    'ReceiverTimeOverHeadView',
]


class ReceiverTimeOverHeadView(JsonFormView):
    """
    获取该地址送达时间开销
    """
    error_messages = {
        'args_error_overflow':
            u'最多支持%s组查询' %
            str(app.config.get('RECEIVER_TIME_SQL_MAX_ONCE', 20)),
    }

    methods = ['POST', ]
    decorators = []
    form_class = ReceiverTimeForm

    def form_valid(self, form):
        start_time = time.time()
        receiver_info_list = form.data['receiverInfoList']

        if len(receiver_info_list) > \
                app.config.get('RECEIVER_TIME_SQL_MAX_ONCE', 20):
            self.update_errors(self.error_messages['args_error_overflow'])
            return self.render_to_response()

        res_receiver_time_list = []
        try:
            res_receiver_time_list = get_receiver_time_overhead_value_list(
                receiver_info_list)
        except:
            sentry.captureException()

        end_time = time.time()
        info = {
            "req_list": receiver_info_list,
            "now_timestamp": datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            "time_used": round(end_time - start_time, 3)
        }
        kafkaBizLogger.info(kafka_event.DYNAMIC_PICKUP_TIME_EVENT, info)

        context = {'receiverTimeList': [
            {'receiverLng': res_info['receiverLng'],
             'receiverLat': res_info['receiverLat'],
             'cityId': res_info['cityId'],
             'receiverTimeValue': res_info['receiverTimeValue'],
             'receiverTimeRank': res_info['receiverTimeRank']}
            for res_info in res_receiver_time_list]}

        return self.render_to_response(context)
