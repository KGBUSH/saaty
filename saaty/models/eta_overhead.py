#!/usr/bin/python
# -*- coding: utf-8 -*-

from core import db
from core.models import Model



class ETATransporterInfo(Model):
    """
    达达eta相关信息表，目前只有A段，后期补充B，C段的字段到数据库
    """
    __tablename__ = "algo_transporter_delivery_history"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    __bind_key__ = "saaty_db"

    id = db.Column(db.Integer, primary_key=True, nullable=False)                 # 主键ID
    transporter_id = db.Column(db.BigInteger, primary_key=True, nullable=False)  # 达达ID
    history_order_num = db.Column(db.Integer, nullable=False)                    # 达达历史接单数
    avg_a1_time = db.Column(db.Integer, nullable=False)                          # 达达平均 接单到到店的路上时间
    avg_a2_time = db.Column(db.Integer)                                          # 达达平均 到店到取货的等待时间
    city_id = db.Column(db.Integer)                                              # 城市ID
    create_time = db.Column(db.TIMESTAMP)                                        # 创建时间
    update_time = db.Column(db.TIMESTAMP)                                        # 更新时间


class ETASupplierInfo(Model):
    """
    商家eta相关信息表，目前只有A段，后期补充B，C段的字段到数据库
    """
    __tablename__ = "algo_supplier_delivery_history"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    __bind_key__ = "saaty_db"

    id = db.Column(db.Integer, primary_key=True, nullable=False)                 # 主键ID
    supplier_id = db.Column(db.BigInteger, primary_key=True, nullable=False)     # 商家ID
    history_order_num = db.Column(db.Integer, nullable=False)                    # 商家历史接单数
    avg_a1_time = db.Column(db.Integer, nullable=False)                          # 商家历史订单中，骑手接单到到店的平均路上时间
    avg_a2_time = db.Column(db.Integer)                                          # 商家历史订单中，骑手到店到取货的平均等待时间
    city_id = db.Column(db.Integer)                                              # 城市ID
    create_time = db.Column(db.TIMESTAMP)                                        # 创建时间
    update_time = db.Column(db.TIMESTAMP)                                        # 更新时间


