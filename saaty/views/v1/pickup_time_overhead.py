# -*- coding: utf-8 -*-
import datetime
import time
from core import app
from core import sentry
from core import kafkaBizLogger
from core import algoKafkaLogger
from common.framework.views import JsonFormView
from saaty.constants import kafka_event
from saaty.forms.poi_time_value_form import SupplierPickupTimeForm
from saaty.services.poi_time_value_service import \
    get_pickup_time_overhead_value_list
from saaty.services import eta_service

__all__ = [
    'PickupTimeOverHeadView',
]


class PickupTimeOverHeadView(JsonFormView):
    """
    获取该商户取货时间开销
    """
    error_messages = {
        'args_error_overflow':
            u'最多支持%s组查询' % str(app.config.get('PICKUP_TIME_SQL_MAX_ONCE', 20)),
    }

    methods = ['POST', ]

    decorators = []
    form_class = SupplierPickupTimeForm

    def form_valid(self, form):
        start_time = time.time()
        form_data = form.data
        supplier_info_list = form_data['supplierInfoList']

        if len(supplier_info_list) > \
                app.config.get('PICKUP_TIME_SQL_MAX_ONCE', 20):
            self.update_errors(self.error_messages['args_error_overflow'])
            return self.render_to_response()

        # 抛出异常直接走老算法
        if eta_service.is_new_eta_call(param_list_dict=supplier_info_list, flag='recOrderId'):
            # 1. 得到test_id
            abtest_id_list = []
            for item in supplier_info_list:
                abtest_id = eta_service.get_recommend_abtest_id(recommend_id=item['recOrderId'])
                abtest_id_list.append(abtest_id)

            try:
                # 2. ABtest
                blank_req_list, experiment_req_list, res_blank_list, res_experiment_list = \
                    eta_service.eta_pickup_cut_abtest(test_id_list=abtest_id_list,
                                                      param_data_dict_list=supplier_info_list)

                # 3. log记录
                time_used = round(time.time() - start_time, 3)
                now_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # 对照组日志
                for blank_req, res_blank_info in zip(blank_req_list, res_blank_list):
                    info = {}
                    info.update({
                        'is_success': 1,
                        'test_id': eta_service.BLANK_ABTEST_ID,
                        "now_timestamp": now_timestamp,
                        "time_used": time_used
                    })
                    info.update(blank_req)
                    info.update({
                        'isDowngrade': res_blank_info['isDowngrade'],
                        'pickupTimeValue': res_blank_info['pickupTimeValue'],
                        'pickupTimeRank': res_blank_info['pickupTimeRank']
                    })
                    algoKafkaLogger.info(kafka_event.ETA_ACCEPT_TO_ARRIVE_TOFETCH_EVENT, info)
                # 实验组日志
                for expe_req, res_expe_info in zip(experiment_req_list, res_experiment_list):
                    info = {}
                    info.update({
                        'is_success': 1,
                        'test_id': 'new',
                        "now_timestamp": now_timestamp,
                        "time_used": time_used
                    })
                    info.update(expe_req)
                    info.update({
                        'isDowngrade': 0 if res_expe_info[0] != -1 else 1,  # 新算法的状态标志1说明没有降级, -1 说明新算法降级；isDowngrade==0: 没有降级
                        'pickupTimeValue': res_expe_info[2],  # 只要取货时间；a1不返回了
                        'pickupTimeRank': -999
                    })
                    algoKafkaLogger.info(kafka_event.ETA_ACCEPT_TO_ARRIVE_TOFETCH_EVENT, info)
            except:
                sentry.captureException()
                info = {'is_success': 0, 'count': len(supplier_info_list)}
                algoKafkaLogger.info(kafka_event.ETA_DELIVERY_EVENT, info)
                # self.update_errors(self.error_messages['args_error'])
                # return self.render_to_response()

        # 4. 老算法返回全量结果
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
        algoKafkaLogger.info(kafka_event.DYNAMIC_PICKUP_TIME_EVENT, info)

        context = {'pickupTimeList': [
            {'isDowngrade': res_info['isDowngrade'],
             'pickupTimeValue': res_info['pickupTimeValue'],
             'pickupTimeRank': res_info['pickupTimeRank']}
            for res_info in res_pickup_time_list
        ]}

        return self.render_to_response(context)
