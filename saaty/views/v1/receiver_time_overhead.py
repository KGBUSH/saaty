# -*- coding: utf-8 -*-
import datetime
import time
from common.framework.views import JsonFormView
from core import app
from core import sentry
from core import kafkaBizLogger
from core import algoKafkaLogger
from saaty.constants import kafka_event
from saaty.forms.poi_time_value_form import ReceiverTimeForm
from saaty.services.poi_time_value_service import \
    get_receiver_time_overhead_value_list
from saaty.services import eta_service

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

        # 抛出异常直接走老算法
        if eta_service.is_new_eta_call(param_list_dict=receiver_info_list, flag='recOrderId'):
            # 1. 得到test_id
            abtest_id_list = []
            for item in receiver_info_list:
                abtest_id = eta_service.get_recommend_abtest_id(recommend_id=item['recOrderId'])
                abtest_id_list.append(abtest_id)

            try:
                # 2. ABtest
                blank_req_list, experiment_req_list, res_blank_list, res_experiment_list = \
                    eta_service.eta_receive_cut_abtest(test_id_list=abtest_id_list,
                                                       param_data_dict_list=receiver_info_list)
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
                        'receiverTimeValue': res_blank_info['receiverTimeValue'],
                        'receiverTimeRank': res_blank_info['receiverTimeRank']
                    })
                    # algoKafkaLogger.info(kafka_event.ETA_DELIVERY_EVENT, info)
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
                        'isDowngrade': 0 if res_expe_info[0] != -1 else 1,  # 新算法的状态标志1说明没有降级,
                        'receiverTimeValue': res_expe_info[1],
                        'receiverTimeRank': -999
                    })
                    # algoKafkaLogger.info(kafka_event.ETA_DELIVERY_EVENT, info)
            except:
                sentry.captureException()
                info = {'is_success': 0, 'count': len(receiver_info_list)}
                algoKafkaLogger.info(kafka_event.ETA_DELIVERY_EVENT, info)
                # self.update_errors(self.error_messages['args_error'])
                # return self.render_to_response()

        res_receiver_time_list = get_receiver_time_overhead_value_list(
            receiver_info_list)

        end_time = time.time()
        info = {
            "req_list": receiver_info_list,
            "now_timestamp": datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            "time_used": round(end_time - start_time, 3)
        }
        kafkaBizLogger.info(kafka_event.DYNAMIC_RECEIVER_TIME_EVENT, info)
        algoKafkaLogger.info(kafka_event.DYNAMIC_RECEIVER_TIME_EVENT, info)

        context = {'receiverTimeList': [
            {'isDowngrade': res_info['isDowngrade'],
             'receiverTimeValue': res_info['receiverTimeValue'],
             'receiverTimeRank': res_info['receiverTimeRank']}
            for res_info in res_receiver_time_list]}

        return self.render_to_response(context)
