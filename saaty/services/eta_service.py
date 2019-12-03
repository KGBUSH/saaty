# -*- coding: utf-8 -*-


from saaty.utils.utils import load_object
from saaty.utils.map_utils import get_distance_meter

import traceback
import numpy as np
import pandas as pd

from common.db import read
from core import db
from core import app
from core import sentry
from saaty.models.eta_overhead import ETASupplierInfo
from saaty.models.eta_overhead import ETATransporterInfo


__all__ = [
    'get_eta_a_overhead_v2',
    'get_eta_a_batch_overhead'
]

PROJECT_PATH = app.config['PROJECT_PATH']

# eta模型
# 针对接单到到店这段时间的模型
model_eta_a1 = load_object(PROJECT_PATH + "/saaty/resource_data/eta/a/from157_tree80/lgb_m1_from157_tree80.pkl")
# 针对到店到取货这段时间的模型
model_eta_a2 = load_object(PROJECT_PATH + "/saaty/resource_data/eta/a/from157_tree80/lgb_m2_from157_tree80.pkl")
# 上述两个模型的feature是共用的，one_hot_columns代表one-hot之后的总feature，保存的是x_train.columns（pandas）
one_hot_columns = load_object(PROJECT_PATH + "/saaty/resource_data/eta/a/from157_tree80/A_params_after_onehot.pkl")

# 需要做one-hot的feature (不一定都在当前版本的特征里)
category = [
    'weekday',
    'hour_minute',
    'hour',
    'cargo_type_id',
    'dada_grade',
    'city_id',
    'supplier_type_id'
]

# v2 ETA-A 的特征
A_v2_features = [
    # 距离
    'real_time_line_distance',
    # t相关属性
    't_history_order_num', 't_avg_a1_time', 't_avg_a2_time',
    # s相关属性
    's_history_order_num', 's_avg_a1_time', 's_avg_a2_time',
    # cargo
    'cargo_type_id', 'cargo_weight',
    # 时间
    'hour', 'weekday', 'is_weekend',
    # 城市
    'city_id'
]


def get_eta_a_batch_overhead(order_list):
    """
    a 段的eta预估，batch
    :param order_list:
    :return:
    """
    results = []
    for item in order_list:
        transporter_id = item['transporter_id']
        transporter_lat = item['transporter_lat']
        transporter_lng = item['transporter_lng']
        supplier_id = item['supplier_id']
        supplier_lat = item['supplier_lat']
        supplier_lng = item['supplier_lng']
        hour = item['hour']
        city_id = item['city_id']
        weekday = item['weekday']
        cargo_type_id = item['cargo_type_id']
        cargo_weight = item['cargo_weight']
        [status, pred_a1, pred_a2] = get_eta_a_overhead_v2(transporter_id, transporter_lat, transporter_lng,
                                                           supplier_id, supplier_lat, supplier_lng,
                                                           hour, city_id, weekday,
                                                           cargo_type_id, cargo_weight
                                                           )
        results.append([status, pred_a1, pred_a2])
    return results


def get_eta_a_overhead_v2(transporter_id, transporter_lat, transporter_lng,
                          supplier_id, supplier_lat, supplier_lng,
                          hour, city_id, weekday,
                          cargo_type_id, cargo_weight):
    """
    v2 版本。去掉了map距离
    a 段的eta预估
    return: [status, a1, a2]
    """
    dada_speed_map = app.config.get('ETA_DADA_SPEED_CITY_GROUP', {})
    default_dada_speed = dada_speed_map.get(0, 4.5)
    dada_speed = dada_speed_map.get(city_id, default_dada_speed)

    default_poi_time_config = app.config.get('POI_TIME_OVERHEAD_DEFAULT_VALUE_DEFAULT_CITY', {})
    city_poi_time_config_map = app.config.get('POI_TIME_OVERHEAD_DEFAULT_VALUE', {})
    city_poi_time_config = city_poi_time_config_map.get(str(city_id), default_poi_time_config)
    pickup_time = city_poi_time_config.get('pickup_time', 100)

    status = -1  # 返回状态

    # 1 获取t->s直线距离，2 map 距离已弃用
    distance_line_dada_to_supplier = get_distance_meter(lat1=transporter_lat, lng1=transporter_lng,
                                           lat2=supplier_lat, lng2=supplier_lng)

    # 3 读数据库查历史记录
    search = {'supplier_id': supplier_id,
              'transporter_id': transporter_id,
              'city_id': city_id}
    try:
        result = get_one_sample_info_from_database_only_transporter_and_supplier(info_dict=search)
        result.update(
            {'real_time_line_distance': distance_line_dada_to_supplier,
             'hour': hour,
             'weekday': weekday,
             "is_weekend": 0 if weekday <= 4 else 1,
             'cargo_type_id': cargo_type_id,
             'cargo_weight': cargo_weight
             })
    except:
        sentry.captureException()
        # 返回老算法
        return [status, distance_line_dada_to_supplier * 1.36 / dada_speed, pickup_time]

    # 4 inference
    # 4.1 preprocess
    x_test = preprocess_for_A_inference(data_dict=result)
    # 4.2 predict
    if x_test is not None:
        status = 1
        y_predict_a1 = model_eta_a1.predict(x_test)  # 预测 达达接单到到店的时间
        y_predict_a2 = model_eta_a2.predict(x_test)  # 预测 达达到店到取货的等待时间
        y_predict_a1 = np.expm1(y_predict_a1)  # 偏态校正
        y_predict_a2 = np.expm1(y_predict_a2)
        return [status, y_predict_a1[0], y_predict_a2[0]]
    else:
        # 返回老算法
        return [status, distance_line_dada_to_supplier * 1.36 / dada_speed, pickup_time]


def preprocess_for_A_inference(data_dict):
    """
    eta accept到pickup（A段） inference之前的预处理
    """
    # 特征对齐
    try:
        x = pd.DataFrame(np.zeros((1, one_hot_columns.values.shape[0])), columns=one_hot_columns)  # empty
        for raw_col in A_v2_features:
            if raw_col in category:
                cal_after = raw_col + '_' + str(data_dict[raw_col])
                x.loc[0, cal_after] = 1
            else:
                # 数值特征
                x.loc[0, raw_col] = data_dict[raw_col]
        return x
    except:
        traceback.print_exc()
        sentry.captureException()
        return None


@read()
def get_one_sample_info_from_database_only_transporter_and_supplier(info_dict):
    """
    从数据库中获取数据
    * 只拿达达表和 商家表，不再拿合作表
    :param info_dict: 只是一个样本
    :return: database_res_list 正确返回只有一个item
    """
    supplier_res = ETASupplierInfo.query \
        .filter(db.and_(ETASupplierInfo.supplier_id == info_dict["supplier_id"],
                        ETASupplierInfo.city_id == info_dict["city_id"])
                ).first()

    transporter_res = ETATransporterInfo.query \
        .filter(db.and_(ETATransporterInfo.transporter_id == info_dict["transporter_id"],
                        ETATransporterInfo.city_id == info_dict["city_id"]
                        )
                ).first()

    database_res = None
    if supplier_res is not None and \
            transporter_res is not None:
        database_res = {
            "supplier_id": supplier_res.supplier_id,
            "s_history_order_num": supplier_res.history_order_num,
            "s_avg_a1_time": supplier_res.avg_a1_time,
            "s_avg_a2_time": supplier_res.avg_a2_time,

            "transporter_id": transporter_res.transporter_id,
            "t_history_order_num": transporter_res.history_order_num,
            "t_avg_a1_time": transporter_res.avg_a1_time,
            "t_avg_a2_time": transporter_res.avg_a2_time,

            "city_id": supplier_res.city_id,
        }
    return database_res
