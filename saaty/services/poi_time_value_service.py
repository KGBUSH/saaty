#!/user/bin/python
# -*- coding: utf-8 -*-

from common.db import read
from core import db
from saaty.models.poi_time_overhead import POISupplierTimeOverhead
from saaty.models.poi_time_overhead import POIReceiverTimeOverhead


@read()
def get_pickup_time_overhead_value_list(req_list=[]):
    """
    读取取货时间开销
    :param req_list:
    :return:
    """
    pickup_time_result_list = []
    pickup_time_result_list = POISupplierTimeOverhead.query \
        .filter(db.or_(db.and_(POISupplierTimeOverhead.supplier_id ==
                               info_list["supplierId"],
                               POISupplierTimeOverhead.supplier_lng ==
                               info_list["supplierLng"],
                               POISupplierTimeOverhead.supplier_lat ==
                               info_list["supplierLat"],
                               POISupplierTimeOverhead.city_id ==
                               info_list["cityId"])
                       for info_list in req_list)).all()

    context = []
    if len(pickup_time_result_list) > 0:
        for res_info in pickup_time_result_list:
            context.append({"supplierLng": str(res_info.supplier_lng),
                            "supplierLat": str(res_info.supplier_lat),
                            "pickupTimeValue": float(res_info.pickup_time),
                            "pickupTimeRank": float(res_info.time_rank)
                            })
    return context


@read()
def get_receiver_time_overhead_value_list(req_list=[]):
    """
    读取送达时间开销
    :param req_list:
    :return:
    """
    receiver_time_result_list = []
    receiver_time_result_list = POIReceiverTimeOverhead.query \
        .filter(db.or_(db.and_(POIReceiverTimeOverhead.receiver_lng ==
                               info_list["receiverLng"],
                               POIReceiverTimeOverhead.receiver_lat ==
                               info_list["receiverLat"],
                               POIReceiverTimeOverhead.city_id ==
                               info_list["cityId"])
                       for info_list in req_list)).all()

    context = []
    if len(receiver_time_result_list) > 0:
        for res_info in receiver_time_result_list:
            context.append({"receiverLng": str(res_info.receiver_lng),
                            "receiverLat": str(res_info.receiver_lat),
                            "receiverTimeValue": float(res_info.receiver_time),
                            "receiverTimeRank": float(res_info.time_rank)
                            })

    return context
