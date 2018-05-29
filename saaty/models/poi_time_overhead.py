#!/usr/bin/python
# -*- coding: utf-8 -*-

from core import db
from core.models import Model


class POISupplierTimeOverhead(Model):
    """
    取货时间开销 数据库模型
    """
    __table_name__ = "poi_supplier_time_overhead"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8"}
    __bind_key__ = "saaty"

    id = db.Column(db.Integer, primary_key=True, nullable=False)  # 主键ID
    supplier_id = db.Column(db.BigInteger)  # 商户ID
    supplier_lng = db.Column(db.VARCHAR, index=True, nullable=False)  # 发货地经度
    supplier_lat = db.Column(db.VARCHAR, index=True, nullable=False)  # 发货地纬度
    city_id = db.Column(db.Integer)  # 城市id
    pickup_time = db.Column(db.Float)  # 取货时间开销
    time_rank = db.Column(db.Float)  # 该时间在城市排名
    create_time = db.Column(db.TIMESTAMP)  # 创建时间
    update_time = db.Column(db.TIMESTAMP)  # 更新时间


class POIReceiverTimeOverhead(Model):
    """
    送达时间开销 数据库模型
    """
    __table_name__ = "poi_receiver_time_overhead"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8"}
    __bind_key__ = "saaty"

    id = db.Column(db.Integer, primary_key=True, nullable=False)  # 主键ID
    receiver_lng = db.Column(db.VARCHAR, index=True, nullable=False)  # 收货地经度
    receiver_lat = db.Column(db.VARCHAR, index=True, nullable=False)  # 收货地纬度
    city_id = db.Column(db.Integer)  # 城市id
    receiver_time = db.Column(db.Float)  # 收货时间开销
    time_rank = db.Column(db.Float)  # 该时间在城市排名
    create_time = db.Column(db.TIMESTAMP)  # 创建时间
    update_time = db.Column(db.TIMESTAMP)  # 更新时间
    geohash = db.Column(db.VARCHAR, index=True, nullable=False)  # geohash

# if __name__ == '__main__':
#
#     req_list = [
#         {"city_id": 1, "supplier_id": 23624, "supplier_lng": 121.446898,
#          "supplier_lat": 31.267098},
#         {"city_id": 1, "supplier_id": 290526, "supplier_lng": 121.544036,
#          "supplier_lat": 31.268749},
#         {"city_id": 1, "supplier_id": 71941, "supplier_lng": 121.474709,
#          "supplier_lat": 31.268248}
#     ]
#
#     pickup_time_result_list = 0.0
#
#     pickup_time_result_list = POISupplierTimeOverhead.query \
#         .filter(db.or_(db.and_(POISupplierTimeOverhead.supplier_id ==
#                                info_list["supplier_id"],
#                                POISupplierTimeOverhead.supplier_lng ==
#                                info_list["supplier_lng"],
#                                POISupplierTimeOverhead.supplier_lat ==
#                                info_list["supplier_lat"],
#                                POISupplierTimeOverhead.city_id == info_list[
#                                    "city_id"])
#                        for info_list in req_list)).all()
#
#     if pickup_time_result_list:
#         print(pickup_time_result_list)
#         for info in pickup_time_result_list:
#             print(info.pickup_time, info.time_rank)

# req_list = [{"city_id": 1, "receiver_lng": 121.557901,
#              "receiver_lat": 31.293715},
#             {"city_id": 1, "receiver_lng": "121.557877",
#              "receiver_lat": 31.290403},
#             {"city_id": 1, "receiver_lng": 121.557251,
#              "receiver_lat": "31.292137"}]
#
# receiver_time_result_list = POIReceiverTimeOverhead.query \
#     .filter(db.or_(db.and_(POIReceiverTimeOverhead.receiver_lng ==
#                            info_list["receiver_lng"],
#                            POIReceiverTimeOverhead.receiver_lat ==
#                            info_list["receiver_lat"],
#                            POIReceiverTimeOverhead.city_id ==
#                            info_list["city_id"])
#                    for info_list in req_list)).all()
#
# if len(receiver_time_result_list) > 0:
#     print(receiver_time_result_list)
#     for info in receiver_time_result_list:
#         print(info.receiver_time, info.time_rank)
