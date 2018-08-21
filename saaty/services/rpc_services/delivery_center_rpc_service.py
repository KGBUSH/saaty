# -*- coding: utf-8 -*-

from core import app
from core.discovery import service_facade
from core.config.service_repos import SERVICE_RPC_DELIVERY_CENTER
from core.config.service_repos import ORDER_DETAIL_SINGLE, ORDER_DETAIL_BATCH
# from dos.toolbox.utils import send_error_log
import json
import math

__all__ = [
    'get_order_detail_single',
    'get_order_detail_batch'
]


def _get_delivery_center_timeout():
    return app.config.get('DELIVERY_CENTER_RPC_TIMEOUT', 1)


def get_order_detail_single(order_id):
    """
    订单详情单个查询
    接口文档见 http://confluence.corp.imdada.cn/pages/viewpage.action?pageId=7574999
    """
    params = {
        'order_id': order_id
    }

    send_result = False
    order_detail = {}

    try:
        result = service_facade.post(
            category=SERVICE_RPC_DELIVERY_CENTER,
            service_name=ORDER_DETAIL_SINGLE,
            data=json.dumps(params),
            headers={'Content-Type': 'application/json', },
            timeout=_get_delivery_center_timeout(),
        )

        if result.get('status', 'fail') == 'ok':
            send_result = True
            content = result.get('content', {})
            order_detail = content.get('order', {})
    except:
        send_result = False
        order_detail = {}

    return send_result, order_detail


def get_order_detail_batch(order_id_list):
    """
    订单详情批量查询
    接口文档见 http://confluence.corp.imdada.cn/pages/viewpage.action?pageId=6924981
    """
    order_info_list = []
    order_group_num = int(math.ceil(float(len(order_id_list)) / 50))

    for i in range(order_group_num):
        order_ids = order_id_list[i * 50:(i + 1) * 50]
        params = {'order_ids': order_ids}
        try:
            rs = service_facade.post(
                category=SERVICE_RPC_DELIVERY_CENTER,
                service_name=ORDER_DETAIL_BATCH,
                data=json.dumps(params),
                headers={'Content-Type': 'application/json', },
                timeout=_get_delivery_center_timeout(),
            )
        except Exception, e:
            rs = {}

        order_info_list = order_info_list + rs.get('content', [])

    # 如果存在某个订单查不到订单详细信息则报错
    if len(order_id_list) != len(order_info_list):
        available_order_id_list = [order_info['id'] for order_info in order_info_list]
        remain_order_id_list = list(set(order_id_list).difference(set(available_order_id_list)))
        # send_error_log("can not get some order detail", remain_order_id_list)

    return order_info_list


if __name__ == '__main__':
    pass
