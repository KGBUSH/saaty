# -*- coding: utf-8 -*-

from core import app
from core import service_facade
from core.config.service_repos import SERVICE_RPC_HUBBLE_POI
from core.config.service_repos import LNG_LAT_POI_ID, ADDRESS_POI_ID, ADDRESS_POI_ID_NO_DIFFICULTY

__all__ = [
    'get_poi_id'
]


def _get_hubble_timeout():
    return app.config.get('TIMEOUT_RPC_HUBBLE_POI', 1)


def get_poi_id(lat, lng, address):
    """
    订单详情单个查询
    接口文档见 http://confluence.corp.imdada.cn/pages/viewpage.action?pageId=8207920
    """
    query_params = {
        'lat': lat,
        'lng': lng,
        'address': address
    }

    send_result = False
    content = {}

    try:
        result = service_facade.get(
            category=SERVICE_RPC_HUBBLE_POI,
            service_name=LNG_LAT_POI_ID,
            query_params=query_params,
            timeout=_get_hubble_timeout(),
        )

        if result.get('status', 'fail') == 'ok':
            send_result = True
            content = result.get('content', {})
    except:
        send_result = False
        content = {}

    return send_result, content


def get_poi_id_no_difficulty(lat, lng, address=None):
    """
    订单详情单个查询
    http://confluence.corp.imdada.cn/pages/viewpage.action?pageId=18588534
    如果达达poi库不存在是否允许到腾讯地图去拿POI
    """
    query_params = {
        'lat': lat,
        'lng': lng,
        'address': address,
        'enable_map': 1
    }

    send_result = False
    content = {}

    try:
        result = service_facade.get(
            category=SERVICE_RPC_HUBBLE_POI,
            service_name=ADDRESS_POI_ID_NO_DIFFICULTY,
            query_params=query_params,
            timeout=_get_hubble_timeout(),
        )

        if result.get('status', 'fail') == 'ok':
            send_result = True
            content = result.get('content', {})
    except:
        send_result = False
        content = {}

    return send_result, content


if __name__ == '__main__':
    pass
