# -*- coding: utf-8 -*-
import datetime
import time
from core import sentry
from core import kafkaBizLogger
from common.framework.views import JsonFormView
from saaty.constants import kafka_event
from saaty.forms.poi_time_value_form import SupplierPickupTimeForm
from saaty.services.poi_time_value_service import \
    get_pickup_time_overhead_value_list

__all__ = [
    'PickupTimeOverHeadView',
]


class PickupTimeOverHeadView(JsonFormView):
    """
    获取该商户取货时间开销
    """
    error_messages = {
        'args_error_overflow': u'最多支持20组查询',
    }

    methods = ['POST', ]

    decorators = []
    form_class = SupplierPickupTimeForm

    def form_valid(self, form):
        start_time = time.time()
        form_data = form.data
        supplier_info_list = form_data['supplierInfoList']

        if len(supplier_info_list) > 20:
            self.update_errors(self.error_messages['args_error_overflow'])
            return self.render_to_response()

        res_pickup_time_list = []
        try:
            res_pickup_time_list = get_pickup_time_overhead_value_list(
                supplier_info_list)
        except:
            sentry.captureException()

        end_time = time.time()
        info = {
            "req_list": supplier_info_list,
            "now_timestamp": datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            "time_used": round(end_time - start_time, 3)
        }
        kafkaBizLogger.info(kafka_event.DYNAMIC_PICKUP_TIME_EVENT, info)

        context = {'pickupTimeList': [
            {'cityId': res_info['cityId'],
             'supplierId': res_info['supplierId'],
             'supplierLng': res_info['supplierLng'],
             'supplierLat': res_info['supplierLat'],
             'pickupTimeValue': res_info['pickupTimeValue'],
             'pickupTimeRank': res_info['pickupTimeRank']}
            for res_info in res_pickup_time_list
        ]}

        return self.render_to_response(context)
