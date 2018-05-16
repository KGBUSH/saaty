#!/user/bin/python
# -*- coding: utf-8 -*-

from common.db import read
from core import db
from core import cache
from core import app
from core import sentry
from saaty.constants import cache_keys
from saaty.constants import cache_expire
from saaty.models.poi_time_overhead import POISupplierTimeOverhead
from saaty.models.poi_time_overhead import POIReceiverTimeOverhead

__all__ = [
    "get_pickup_time_overhead_value_list",
    "get_receiver_time_overhead_value_list"
]


@read()
def get_pickup_time_use_database(req_list=[]):
    database_res_tmp = POISupplierTimeOverhead.query \
        .filter(db.or_(db.and_(POISupplierTimeOverhead.supplier_id ==
                               info_list["supplierId"],
                               POISupplierTimeOverhead.supplier_lng ==
                               info_list["supplierLng"],
                               POISupplierTimeOverhead.supplier_lat ==
                               info_list["supplierLat"],
                               POISupplierTimeOverhead.city_id ==
                               info_list["cityId"])
                       for info_list in req_list)).all()

    req_dict = {}
    if len(database_res_tmp) > 0:
        for res_info in database_res_tmp:
            kwargs = {
                "supplierId": res_info.supplier_id,
                "supplierLng": res_info.supplier_lng,
                "supplierLat": res_info.supplier_lat,
                "cityId": res_info.city_id
            }
            key_info = cache_keys.CACHE_KEY_PICKUP_TIME_OVERHEAD.format(
                **kwargs)
            req_dict[key_info] = res_info

    database_res = []

    local_cfg = app.config.get('POI_TIME_OVERHEAD_DEFAULT_VALUE', {})

    # 查询不到的数据，使用默认值
    for req_info in req_list:
        key_req = cache_keys.CACHE_KEY_PICKUP_TIME_OVERHEAD.format(**req_info)

        if key_req in req_dict:
            res_info = req_dict[key_req]
            database_res.append({'pickupTimeValue':
                                     float(res_info.pickup_time),
                                 'pickupTimeRank':
                                     float(res_info.time_rank),
                                 'isDowngrade': int(0),
                                 'cityId': req_info['cityId'],
                                 'supplierId': req_info['supplierId'],
                                 'supplierLng': req_info['supplierLng'],
                                 'supplierLat': req_info['supplierLat']})
        else:
            local_city_info = local_cfg[req_info["cityId"]]
            database_res.append({'pickupTimeValue':
                                     float(local_city_info["pickup_time"]),
                                 'pickupTimeRank':
                                     float(local_city_info["pickup_rank"]),
                                 'isDowngrade': int(1),
                                 'cityId': req_info['cityId'],
                                 'supplierId': req_info['supplierId'],
                                 'supplierLng': req_info['supplierLng'],
                                 'supplierLat': req_info['supplierLat']})
    return database_res


def get_pickup_time_overhead_value_list(req_list=[]):
    """
    读取取货时间开销
    :param req_list:
    :return:
    """
    tmp_pickup_time_result_list = []

    # 优先从缓存中读取
    not_in_cache = []
    try:
        keys = [cache_keys.CACHE_KEY_PICKUP_TIME_OVERHEAD.format(
            **supplier_info) for supplier_info in req_list]
        cache_res = cache.get_many(*keys)
        for index, cache_obj in enumerate(cache_res):
            if cache_obj is None:
                not_in_cache.append(req_list[index])
            else:
                tmp_pickup_time_result_list.append(cache_obj)
    except:
        sentry.captureException()

    # 缓存中不存在的，使用数据库查询
    if len(not_in_cache) > 0:
        database_res = get_pickup_time_use_database(not_in_cache)
        if len(database_res) > 0:
            for res in database_res:
                tmp_pickup_time_result_list.append(res)

            try:
                # 新查询的数据写入缓存
                need_cache_info = {
                    cache_keys.CACHE_KEY_PICKUP_TIME_OVERHEAD.format(
                        **res_info): res_info for res_info in database_res}

                cache.set_many(need_cache_info,
                               timeout=cache_expire.CHCHE_EXPIRE_TIME_ONE_WEEK)
            except:
                sentry.captureException()

    # 按请求list顺序重排
    res_key_value = {
        cache_keys.CACHE_KEY_PICKUP_TIME_OVERHEAD.format(**res_info):
            res_info for res_info in tmp_pickup_time_result_list
    }

    pickup_time_result_list = []
    for req_info in req_list:
        key_req = cache_keys.CACHE_KEY_PICKUP_TIME_OVERHEAD.format(
            **req_info)
        pickup_time_result_list.append(res_key_value[key_req])

    return pickup_time_result_list


@read()
def get_receiver_time_use_database(req_list=[]):
    database_res_tmp = POIReceiverTimeOverhead.query \
        .filter(db.or_(db.and_(POIReceiverTimeOverhead.receiver_lng ==
                               info_list["receiverLng"],
                               POIReceiverTimeOverhead.receiver_lat ==
                               info_list["receiverLat"],
                               POIReceiverTimeOverhead.city_id ==
                               info_list["cityId"])
                       for info_list in req_list)).all()

    req_dict = {}
    if len(database_res_tmp) > 0:
        for res_info in database_res_tmp:
            kwargs = {
                "receiverLng": res_info.receiver_lng,
                "receiverLat": res_info.receiver_lat,
                "cityId": res_info.city_id
            }
            key_info = cache_keys.CACHE_KEY_RECEIVER_TIME_OVERHEAD.format(
                **kwargs)
            req_dict[key_info] = res_info

    database_res = []

    local_cfg = app.config.get('POI_TIME_OVERHEAD_DEFAULT_VALUE', {})

    # 查询不到的数据，使用默认值
    for req_info in req_list:
        key_req = cache_keys.CACHE_KEY_RECEIVER_TIME_OVERHEAD.format(**req_info)

        if key_req in req_dict:
            res_info = req_dict[key_req]
            database_res.append({'receiverTimeValue':
                                     float(res_info.receiver_time),
                                 'receiverTimeRank':
                                     float(res_info.time_rank),
                                 'isDowngrade': int(0),
                                 'receiverLng': req_info['receiverLng'],
                                 'receiverLat': req_info['receiverLat'],
                                 'cityId': req_info['cityId']})
        else:
            local_city_info = local_cfg[req_info["cityId"]]
            database_res.append({'receiverTimeValue':
                                     float(local_city_info["receiver_time"]),
                                 'receiverTimeRank':
                                     float(local_city_info["receiver_rank"]),
                                 'isDowngrade': int(1),
                                 'receiverLng': req_info['receiverLng'],
                                 'receiverLat': req_info['receiverLat'],
                                 'cityId': req_info['cityId']})
    return database_res


def get_receiver_time_overhead_value_list(req_list=[]):
    """
    读取送达时间开销
    :param req_list:
    :return:
    """

    tmp_res_receiver_time_list = []

    # 从缓存中读取
    not_in_cache = []
    try:
        keys = [cache_keys.CACHE_KEY_RECEIVER_TIME_OVERHEAD.format(**req_info)
                for req_info in req_list]
        cache_res = cache.get_many(*keys)
        for index, cache_obj in enumerate(cache_res):
            if cache_obj is None:
                not_in_cache.append(req_list[index])
            else:
                tmp_res_receiver_time_list.append(cache_obj)
    except:
        sentry.captureException()

    # 缓存中不存在的，使用数据库查询
    if len(not_in_cache) > 0:
        database_res = get_receiver_time_use_database(not_in_cache)
        if len(database_res) > 0:
            for res in database_res:
                tmp_res_receiver_time_list.append(res)

                # 写入缓存
            try:
                need_cache_info = {
                    cache_keys.CACHE_KEY_RECEIVER_TIME_OVERHEAD.format(
                        **res_info): res_info for res_info in database_res}

                cache.set_many(need_cache_info,
                               timeout=cache_expire.CHCHE_EXPIRE_TIME_ONE_WEEK)
            except:
                sentry.captureException()

    # 按请求list顺序重排
    res_key_value = {
        cache_keys.CACHE_KEY_RECEIVER_TIME_OVERHEAD.format(**res_info):
            res_info for res_info in tmp_res_receiver_time_list
    }

    res_receiver_time_list = []
    for req_info in req_list:
        key_req = cache_keys.CACHE_KEY_RECEIVER_TIME_OVERHEAD.format(**req_info)
        res_receiver_time_list.append(res_key_value[key_req])

    return res_receiver_time_list
