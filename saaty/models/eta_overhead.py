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


class ETATransporterPeekDeliveryInfo(Model):
    """
    达达的平均交付时间统计，以及高峰低谷的交付统计
    """
    __tablename__ = "algo_transporter_delivery_peek_Info"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    __bind_key__ = "saaty_db"

    id = db.Column(db.Integer, primary_key=True, nullable=False)                 # 主键ID

    transporter_id = db.Column(db.BigInteger, primary_key=True, nullable=False)  # 达达ID
    city_id = db.Column(db.Integer)                                              # 城市ID
    delivery_cnt = db.Column(db.Integer, nullable=False)                         # 骑手交付订单数目
    avg_delivery_time1 = db.Column(db.Integer, nullable=False)                   # 进圈到finish的平均时间
    avg_delivery_time2 = db.Column(db.Integer, nullable=False)                   # 进圈第一条到最后一条上报的平均时间
    per_delivery_time1 = db.Column(db.Integer, nullable=False)                   # 进圈到finish的中位数时间
    per_delivery_time2 = db.Column(db.Integer, nullable=False)                   # 进圈第一条到最后一条上报的中位数时间
    cnt_peek1 = db.Column(db.Integer, nullable=False)                            # 统计高峰阶段的订单量, 主要是午餐晚餐饭点时间
    cnt_peek2 = db.Column(db.Integer, nullable=False)                            # 统计高峰之间的闲时阶段的订单量
    cnt_peek3 = db.Column(db.Integer, nullable=False)                            # 统计半夜到清晨阶段的订单量
    cnt_peek0 = db.Column(db.Integer, nullable=False)                            # 统计其他阶段的订单量
    per_delivery_time1_peek1 = db.Column(db.Integer, nullable=False)             # 统计高峰阶段的中位数时间, 主要是午餐晚餐饭点时间
    per_delivery_time1_peek2 = db.Column(db.Integer, nullable=False)             # 统计高峰之间的闲时阶段的中位数时间
    per_delivery_time1_peek3 = db.Column(db.Integer, nullable=False)             # 统计半夜到清晨阶段的中位数时间
    per_delivery_time1_peek0 = db.Column(db.Integer, nullable=False)             # 统计其他阶段的订单量

    create_time = db.Column(db.TIMESTAMP)                                        # 创建时间
    update_time = db.Column(db.TIMESTAMP)                                        # 更新时间


class ETAPoiStatistics(Model):
    """
    poi 的统计数据
    """
    __tablename__ = "algo_poi_statistic_Info"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    __bind_key__ = "saaty_db"

    id = db.Column(db.Integer, primary_key=True, nullable=False)                     # 主键ID

    poi_id = db.Column(db.VARCHAR, nullable=False)                                   # poi_id
    percentile_delivery_time_poi = db.Column(db.Float)                               # 该poi的中位数交付时间
    avg_delivery_time_poi = db.Column(db.Float)                                      # 该poi的平均交付时间
    percentile_distance_poi = db.Column(db.Float)                                    # 收货地与poi的中位数距离
    std_distance_poi = db.Column(db.Float)                                           # 距离方差
    std_delivery_time_poi = db.Column(db.Float)                                      # 交付时间方差
    order_cnt = db.Column(db.Integer)                                                # 交付数量
    city_id = db.Column(db.Integer)                                                  # 城市ID
    poi_lat = db.Column(db.Float)                                                    # 纬度
    poi_lng = db.Column(db.Float)                                                    # 经度

    create_time = db.Column(db.TIMESTAMP)                                             # 创建时间
    update_time = db.Column(db.TIMESTAMP)                                             # 更新时间
