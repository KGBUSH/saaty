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
from saaty.models.eta_overhead import ETATransporterPeekDeliveryInfo
from saaty.models.eta_overhead import ETAPoiStatistics
from saaty.services.rpc_services.hubble_poi_rpc_service import get_poi_id
from saaty.utils.address_floor import ETABuildingRecognizer

__all__ = [
    'get_eta_a_overhead_v2',
    'get_eta_a_batch_overhead',

    'get_eta_c_overhead'
]

PROJECT_PATH = app.config['PROJECT_PATH']

# eta模型
"""
ETA A 段 （接单到到店，到店到取货）
"""
# 针对接单到到店这段时间的模型
model_dir = "/saaty/resource_data/eta/a/from157_0201to0303_at0309/"
model_eta_a1 = load_object(PROJECT_PATH + model_dir + "lgb_m1.pkl")
# 针对到店到取货这段时间的模型
model_eta_a2 = load_object(PROJECT_PATH + model_dir + "lgb_m2.pkl")
# 上述两个模型的feature是共用的，one_hot_columns代表one-hot之后的总feature，保存的是x_train.columns（pandas）
one_hot_columns_A = load_object(PROJECT_PATH + model_dir + "A_params_after_onehot.pkl")

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

"""
eta C 段 （交付阶段）
"""
# C段模型
model_eta_c = load_object(PROJECT_PATH + "/saaty/resource_data/eta/c/v2/lgb_model.pkl")
# one-hot之后的总feature
feature_extractor_c = load_object(PROJECT_PATH + "/saaty/resource_data/eta/c/v2/lgb_fea_preprocess.pkl")


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
    try:
        if x_test is not None:
            y_predict_a1 = model_eta_a1.predict(x_test)  # 预测 达达接单到到店的时间
            y_predict_a2 = model_eta_a2.predict(x_test)  # 预测 达达到店到取货的等待时间
            y_predict_a1 = np.expm1(y_predict_a1)  # 偏态校正
            y_predict_a2 = np.expm1(y_predict_a2)
            status = 1
            return [status, y_predict_a1[0], y_predict_a2[0]]
        else:
            # 返回老算法
            return [status, distance_line_dada_to_supplier * 1.36 / dada_speed, pickup_time]
    except:
        sentry.captureException()
        # 返回老算法
        return [status, distance_line_dada_to_supplier * 1.36 / dada_speed, pickup_time]


def preprocess_for_A_inference(data_dict):
    """
    eta accept到pickup（A段） inference之前的预处理
    """
    # 特征对齐
    try:
        x = pd.DataFrame(np.zeros((1, one_hot_columns_A.values.shape[0])), columns=one_hot_columns_A)  # empty
        for raw_col in A_v2_features:
            if raw_col in category:
                cal_after = raw_col + '_' + str(data_dict[raw_col])
                if cal_after not in one_hot_columns_A.values:
                    return None
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
    if supplier_res is not None and transporter_res is not None:
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


def get_eta_c_overhead(transporter_id, receiver_address, receiver_lat, receiver_lng,
                       hour, city_id, weekday,
                       cargo_type_id, cargo_weight):
    """
    交付时间预估（C段）
    """
    default_poi_time_config = app.config.get('POI_TIME_OVERHEAD_DEFAULT_VALUE_DEFAULT_CITY', {})
    city_poi_time_config_map = app.config.get('POI_TIME_OVERHEAD_DEFAULT_VALUE', {})
    city_poi_time_config = city_poi_time_config_map.get(str(city_id), default_poi_time_config)
    delivery_time = city_poi_time_config.get('receiver_time', 100)

    status = -1  # 返回状态

    # 0. 骑手高峰低谷交付特征数据获取
    search = {
        'transporter_id': transporter_id,
        'city_id': city_id
    }
    try:
        peak_result = get_transporter_peak_info(info_dict=search)
    except:
        sentry.captureException()
        return [status, delivery_time]
    if peak_result is None:
        return [status, delivery_time]
    # 根据hour字段算出当前peak
    current_cnt_peek = -1
    current_per_delivery_time_peek = -1
    if (11 <= hour < 13) or (18 <= hour < 20):
        current_cnt_peek = peak_result['cnt_peek1']
        current_per_delivery_time_peek = peak_result['per_delivery_time_peek1']
    elif (9 <= hour < 11) or (15 <= hour < 17) or (20 <= hour < 22):
        current_cnt_peek = peak_result['cnt_peek2']
        current_per_delivery_time_peek = peak_result['per_delivery_time_peek2']
    elif (hour < 9) or (23 <= hour):
        current_cnt_peek = peak_result['cnt_peek3']
        current_per_delivery_time_peek = peak_result['per_delivery_time_peek3']
    else:
        current_cnt_peek = peak_result['cnt_peek0']
        current_per_delivery_time_peek = peak_result['per_delivery_time_peek0']
    peak_result['current_cnt_peek'] = current_cnt_peek
    peak_result['current_per_delivery_time_peek'] = current_per_delivery_time_peek

    # 1 查询poi相关信息
    try:
        req_poi_result, poi_content = get_poi_id(lat=receiver_lat, lng=receiver_lng, address=receiver_address)
    except:
        sentry.captureException()
        return [status, delivery_time]
    if req_poi_result:
        receiver_poi_id = poi_content.get("poi_id", 0)
        prob = poi_content.get('prob', 0.0)
        poi_lat = poi_content.get('poi_lat', 0.0)
        poi_lng = poi_content.get('poi_lng', 0.0)
    else:
        return [status, delivery_time]
    if prob < 0.5 or poi_lat <= 0 or poi_lng <= 0:
        return [status, delivery_time]  # poi匹配概率小于阈值
    search = {
        'poi_id': receiver_poi_id,
        'city_id': city_id,
        'poi_lat': poi_lat,
        'poi_lng': poi_lng
        # 'poi_id': 2691071091552944069,
        # 'city_id': 1,
        # 'poi_lat': 31.2281,
        # 'poi_lng': 121.395
    }
    poi_result = get_poi_statistic_info(info_dict=search)
    if poi_result is None:
        return [status, delivery_time]

    # 2 其他基础字段
    other_result = {
        'cargo_type_id': str(cargo_type_id),
        'cargo_weight': cargo_weight,
        # 'receiver_address_char_num': receiver_address.__len__(),
        'hour': str(hour),
        'city_id': str(city_id)
    }

    # 3 合并所有字段
    result = {}
    result.update(peak_result)
    result.update(poi_result)
    result.update(other_result)

    # 4 inference
    try:
        x_test = feature_extractor_c["dict_vector"].transform(result)
        y_predict_c = model_eta_c.predict(x_test)  # 预测 达达接单到到店的时间
        y_predict_c = np.expm1(y_predict_c)  # 偏态校正
        status = 1
        return [status, y_predict_c[0]]
    except:
        sentry.captureException()
        return [status, delivery_time]


@read()
def get_transporter_peak_info(info_dict):
    """
    从hour_peek那个表找到该骑手的相关信息
    :param info_dict:
    :return:
    """
    transporter_peek_res = ETATransporterPeekDeliveryInfo.query \
        .filter(db.and_(ETATransporterPeekDeliveryInfo.transporter_id == info_dict["transporter_id"],
                        ETATransporterPeekDeliveryInfo.city_id == info_dict["city_id"]
                        )
                ).first()
    transporter_res = ETATransporterInfo.query \
        .filter(db.and_(ETATransporterInfo.transporter_id == info_dict["transporter_id"],
                        ETATransporterInfo.city_id == info_dict["city_id"]
                        )
                ).first()

    database_res = None
    if transporter_peek_res is not None and transporter_res is not None:
        database_res = {
            # 高峰低谷特征
            # "transporter_id": transporter_peek_res.transporter_id,
            "city_id": transporter_peek_res.city_id,
            "delivery_cnt": transporter_peek_res.delivery_cnt,
            # "avg_delivery_time1": transporter_peek_res.avg_delivery_time1,
            "avg_delivery_time2": transporter_peek_res.avg_delivery_time2,
            # "per_delivery_time1": transporter_peek_res.per_delivery_time1,
            "per_delivery_time2": transporter_peek_res.per_delivery_time2,
            "cnt_peek1": transporter_peek_res.cnt_peek1,
            "cnt_peek2": transporter_peek_res.cnt_peek2,
            "cnt_peek3": transporter_peek_res.cnt_peek3,
            "cnt_peek0": transporter_peek_res.cnt_peek0,
            "per_delivery_time_peek1": transporter_peek_res.per_delivery_time_peek1,
            "per_delivery_time_peek2": transporter_peek_res.per_delivery_time_peek2,
            "per_delivery_time_peek3": transporter_peek_res.per_delivery_time_peek3,
            "per_delivery_time_peek0": transporter_peek_res.per_delivery_time_peek0,

            # A段特征
            "t_history_order_num": transporter_res.history_order_num,  # 数据库没有前缀t_
            "t_avg_a1_time": transporter_res.avg_a1_time,
            "t_avg_a2_time": transporter_res.avg_a2_time,
        }

    return database_res


@read()
def get_poi_statistic_info(info_dict):
    """ poi 的时间，距离等特征"""

    poi_res = ETAPoiStatistics.query \
        .filter(db.and_(ETAPoiStatistics.poi_id == info_dict["poi_id"],
                        ETAPoiStatistics.city_id == info_dict["city_id"]
                        )
                ).first()

    database_res = None
    if poi_res is not None:
        database_res = {
            # poi特征
            "percentile_delivery_time_poi": poi_res.percentile_delivery_time_poi,  # 和数据库5.2步骤保持统一命名
            "avg_delivery_time_poi": poi_res.avg_delivery_time_poi,
            "percentile_distance_poi": poi_res.percentile_distance_poi,
            "std_distance_poi": poi_res.std_distance_poi,
            "std_delivery_time_poi": poi_res.std_delivery_time_poi,
            "order_cnt": poi_res.order_cnt,
        }
    return database_res
