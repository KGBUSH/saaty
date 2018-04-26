#!/user/bin/python
# -*- coding: utf-8 -*-

from common.db import read
from core import db
from core import cache
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

    database_res = []
    if len(database_res_tmp) > 0:
        for res_info in database_res_tmp:
            database_res.append({'cityId': res_info.city_id,
                                 'supplierId': res_info.supplier_id,
                                 'supplierLng': res_info.supplier_lng,
                                 'supplierLat': res_info.supplier_lat,
                                 'pickupTimeValue': float(
                                     res_info.pickup_time),
                                 'pickupTimeRank': float(
                                     res_info.time_rank)
                                 })
    return database_res


def get_pickup_time_overhead_value_list(req_list=[]):
    """
    读取取货时间开销
    :param req_list:
    :return:
    """
    pickup_time_result_list = []

    # 优先从缓存中读取
    not_in_cache = []
    try:
        keys = [cache_keys.CACHE_KEY_PICKUP_TIME_OVERHEAD.format(
            **supplier_info) for supplier_info in req_list]
        print('keys = ', keys)
        cache_res = cache.get_many(*keys)
        for index, cache_obj in enumerate(cache_res):
            if cache_obj is None:
                not_in_cache.append(req_list[index])
            else:
                pickup_time_result_list.append(cache_obj)
    except:
        sentry.captureException()

    # 缓存中不存在的，使用数据库查询
    if len(not_in_cache) > 0:
        database_res = get_pickup_time_use_database(not_in_cache)
        if len(database_res) > 0:
            for res in database_res:
                pickup_time_result_list.append(res)

            try:
                # 新查询的数据写入缓存
                need_cache_info = {
                    cache_keys.CACHE_KEY_PICKUP_TIME_OVERHEAD.format(
                        **res_info): res_info for res_info in database_res}

                cache.set_many(need_cache_info,
                               timeout=cache_expire.CHCHE_EXPIRE_TIME_ONE_WEEK)
            except:
                sentry.captureException()

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

    database_res = []
    if len(database_res_tmp) > 0:
        for res_info in database_res_tmp:
            database_res.append({'cityId': res_info.city_id,
                                 'receiverLng': res_info.receiver_lng,
                                 'receiverLat': res_info.receiver_lat,
                                 'receiverTimeValue':
                                     float(res_info.receiver_time),
                                 'receiverTimeRank':
                                     float(res_info.time_rank)})

    return database_res


def get_receiver_time_overhead_value_list(req_list=[]):
    """
    读取送达时间开销
    :param req_list:
    :return:
    """

    res_receiver_time_list = []

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
                res_receiver_time_list.append(cache_obj)
    except:
        sentry.captureException()

    # 缓存中不存在的，使用数据库查询
    if len(not_in_cache) > 0:
        database_res = get_receiver_time_use_database(not_in_cache)
        if len(database_res) > 0:
            for res in database_res:
                res_receiver_time_list.append(res)

            # 写入缓存
            try:
                need_cache_info = {
                    cache_keys.CACHE_KEY_RECEIVER_TIME_OVERHEAD.format(
                        **res_info): res_info for res_info in database_res}

                cache.set_many(need_cache_info,
                               timeout=cache_expire.CHCHE_EXPIRE_TIME_ONE_WEEK)
            except:
                sentry.captureException()

    return res_receiver_time_list
