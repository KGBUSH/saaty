#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 xuekun.zhuang <zhuangxuekun@imdada.cn>
from core import db
from core.models import Model


class POISupplierTimeDifficulty(Model):
    __tablename__ = "poi_supplier_time_difficulty"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8"}
    __bind_key__ = "saaty"

    id = db.Column(db.Integer, primary_key=True, nullable=False)    # 主键ID
    supplier_id = db.Column(db.BigInteger)                          # 商户ID
    supplier_lng = db.Column(db.Float, index=True, nullable=False)  # 商户的经度
    supplier_lat = db.Column(db.Float, index=True, nullable=False)  # 商户的纬度
    city_id = db.Column(db.Integer)                                 # 城市ID
    poi_value = db.Column(db.Float)                                 # 难度值
    create_time = db.Column(db.TIMESTAMP)                           #
    update_time = db.Column(db.TIMESTAMP)                           #


class POIReceiverTimeDifficulty(Model):
    __tablename__ = "poi_receiver_time_difficulty"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8"}
    __bind_key__ = "saaty"

    id = db.Column(db.Integer, primary_key=True, nullable=False)    # 主键ID
    receiver_lng = db.Column(db.Float, index=True, nullable=False)  # 收货地的经度
    receiver_lat = db.Column(db.Float, index=True, nullable=False)  # 收货地的纬度
    city_id = db.Column(db.Integer)                                 # 城市ID
    poi_value = db.Column(db.Float)                                 # 难度值
    create_time = db.Column(db.TIMESTAMP)                           #
    update_time = db.Column(db.TIMESTAMP)                           #


if __name__ == "__main__":

    supplier_id = 3665730
    supplier_lng = 121.32576
    supplier_lat = 31.46398

    res = POISupplierTimeDifficulty.query \
        .filter(POISupplierTimeDifficulty.supplier_id == supplier_id,
                POISupplierTimeDifficulty.supplier_lng == supplier_lng,
                POISupplierTimeDifficulty.supplier_lat == supplier_lat) \
        .all()
    print(res)


    receiver_lng = 121.426364
    receiver_lat = 31.319999

    res = POIReceiverTimeDifficulty.query \
        .filter(POIReceiverTimeDifficulty.receiver_lng == receiver_lng,
                POIReceiverTimeDifficulty.receiver_lat == receiver_lat) \
        .all()
    print(res[0].poi_value)