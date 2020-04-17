# -*- coding: utf-8 -*-


from saaty.utils.utils import load_object
from saaty.utils.map_utils import get_distance_meter

import traceback
import numpy as np
import pandas as pd
import time

from common.db import read
from core import db
from core import app
from core import sentry
from saaty.models.eta_overhead import ETASupplierInfo
from saaty.models.eta_overhead import ETATransporterInfo
from saaty.models.eta_overhead import ETATransporterPeekDeliveryInfo
from saaty.models.eta_overhead import ETAPoiStatistics
from saaty.services.rpc_services.hubble_poi_rpc_service import get_poi_id, get_poi_id_no_difficulty, get_poi_id_no_difficulty_batch
from saaty.utils.address_floor import ETABuildingRecognizer
from saaty.utils import abtest
from saaty.services.poi_time_value_service import \
    get_pickup_time_overhead_value_list
from saaty.services.poi_time_value_service import \
    get_receiver_time_overhead_value_list
from saaty.services.rpc_services.delivery_center_rpc_service import \
    get_order_detail_batch, get_order_detail_for_eta_batch

__all__ = [
    'get_eta_a_overhead_v2',
    'get_eta_a_batch_overhead',

    'get_eta_c_overhead',
    'get_eta_c_overhead_v2_batch'
]

BLANK_ABTEST_ID = 'blank'

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

feature_extractor_a = load_object(PROJECT_PATH + "/saaty/resource_data/eta/a/v2/lgb_fea_preprocess.pkl")
model_eta_a1 = load_object(PROJECT_PATH + "/saaty/resource_data/eta/a/v2/lgb_model_a1.pkl")
model_eta_a2 = load_object(PROJECT_PATH + "/saaty/resource_data/eta/a/v2/lgb_model_a2.pkl")

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


def get_eta_a_overhead_v2_batch(search_list):
    """
    eta a段（到店+取货）
    :param search_list: list[dict, dict, ……]
                          transporter_id, transporter_lat, transporter_lng,
                          supplier_id, supplier_lat, supplier_lng,
                          hour, city_id, weekday,
                          cargo_type_id, cargo_weight
    :return:
    """
    all_result_list = []
    line_distance_list = []  # 所有的直线距离
    valid_index_list = []  # 记录有效行数的idx
    valid_item_list = []  # 记录有效item，用于inference

    # 1. 兜底结果
    for i in range(len(search_list)):
        dada_speed_map = app.config.get('ETA_DADA_SPEED_CITY_GROUP', {})
        default_dada_speed = dada_speed_map.get(0, 4.5)
        dada_speed = dada_speed_map.get(search_list[i]['city_id'], default_dada_speed)

        default_poi_time_config = app.config.get('POI_TIME_OVERHEAD_DEFAULT_VALUE_DEFAULT_CITY', {})
        city_poi_time_config_map = app.config.get('POI_TIME_OVERHEAD_DEFAULT_VALUE', {})
        city_poi_time_config = city_poi_time_config_map.get(str(search_list[i]['city_id']), default_poi_time_config)
        pickup_time = city_poi_time_config.get('pickup_time', 100)

        # 1 获取t->s直线距离，2 map 距离已弃用
        distance_line_dada_to_supplier = get_distance_meter(lat1=search_list[i]['transporter_lat'], lng1=search_list[i]['transporter_lng'],
                                                            lat2=search_list[i]['supplier_lat'], lng2=search_list[i]['supplier_lng'])
        line_distance_list.append(distance_line_dada_to_supplier)
        old_result = [-1, distance_line_dada_to_supplier * 1.36 / dada_speed, pickup_time]
        all_result_list.append(old_result)  # 一开始先装兜底结果

    # 2. 读数据库查历史记录
    search_db_list = [{'supplier_id': item['supplier_id'],
                       'transporter_id': item['transporter_id'],
                       'city_id': item['city_id']}
                      for item in search_list]
    try:
        result = get_batch_info_from_database_only_transporter_and_supplier(info_list=search_db_list)
    except:
        sentry.captureException()
        # 数据库连接异常，返回老算法
        return all_result_list

    # 3. 拼接
    for i in range(len(result)):
        item = result[i]
        if item is not None:
            item.update(
                {'real_time_line_distance': line_distance_list[i],
                 'hour': str(search_list[i]['hour']),
                 'weekday': str(search_list[i]['weekday']),
                 "is_weekend": '1' if search_list[i]['weekday'] > 4 else '0',
                 'cargo_type_id': str(search_list[i]['cargo_type_id']),
                 'cargo_weight': search_list[i]['cargo_weight'],

                 'is_over200m': '1' if line_distance_list[i] > 200 else '0',
                 'is_over20m': '1' if line_distance_list[i] > 20 else '0',

                 'old_a1': all_result_list[i][1],
                 'old_a2': all_result_list[i][2]
                 }
            )
            valid_index_list.append(i)
            valid_item_list.append(item)

    # 4 inference
    try:
        x_test = feature_extractor_a["dict_vector"].transform(valid_item_list)  # valid_item_list为[] 会抛出ValueError，属于正常流程
        y_predict_a1 = model_eta_a1.predict(x_test)  # 预测 达达接单到到店的时间  shape=(?, )
        y_predict_a1 = np.expm1(y_predict_a1)  # 偏态校正
        y_predict_a2 = model_eta_a2.predict(x_test)  # 预测 达达到店到取货的时间  shape=(?, )
        y_predict_a2 = np.expm1(y_predict_a2)  # 偏态校正
        for i, valid_id in enumerate(valid_index_list):
            new_result = [1, y_predict_a1[i], y_predict_a2[i]]
            all_result_list[valid_id] = new_result
        return all_result_list
    except:
        sentry.captureException()
        return all_result_list


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


@read()
def get_batch_info_from_database_only_transporter_and_supplier(info_list):
    """
    从数据库中获取数据
    * 只拿达达表和 商家表，
    return: [obj, obj, ……],
            obj: dict 或 None
    """
    # 1. supplier
    supplier_id_list = [info['supplier_id'] for info in info_list]
    supplier_info_obj_list = ETASupplierInfo.query \
        .filter(ETASupplierInfo.supplier_id.in_(list(set(supplier_id_list)))) \
        .all()
    supplier_info_obj_dict = {
        supplier_res.supplier_id: supplier_res for supplier_res in supplier_info_obj_list
    }
    supplier_res_list = [
        supplier_info_obj_dict.get(supplier_id, None) for supplier_id in supplier_id_list
    ]

    # 2. transporter
    transporter_id_list = [info['transporter_id'] for info in info_list]
    transporter_info_obj_list = ETATransporterInfo.query \
        .filter(ETATransporterInfo.transporter_id.in_(list(set(transporter_id_list)))) \
        .all()
    transporter_info_obj_dict = {
        transporter_res.transporter_id: transporter_res for transporter_res in transporter_info_obj_list
    }
    transporter_res_list = [
        transporter_info_obj_dict.get(transporter_id, None) for transporter_id in transporter_id_list
    ]

    # 3. 拼接
    database_res_list = []
    for info, supplier_res, transporter_res in zip(
            info_list, supplier_res_list, transporter_res_list):
        city_id = info['city_id']
        database_res = None
        if supplier_res is not None and transporter_res is not None \
                and city_id == supplier_res.city_id == transporter_res.city_id:
            # 两个数据库查询都不为空且三个city是一致的
            database_res = {
                'supplier_id': supplier_res.supplier_id,
                's_history_order_num': supplier_res.history_order_num,
                's_avg_a1_time': supplier_res.avg_a1_time,
                's_avg_a2_time': supplier_res.avg_a2_time,

                'transporter_id': transporter_res.transporter_id,
                't_history_order_num': transporter_res.history_order_num,
                't_avg_a1_time': transporter_res.avg_a1_time,
                't_avg_a2_time': transporter_res.avg_a2_time,

                'city_id': str(supplier_res.city_id),  # one_hot
            }
        database_res_list.append(database_res)

    return database_res_list


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
        # req_poi_result, poi_content = get_poi_id(lat=receiver_lat, lng=receiver_lng, address=receiver_address)
        req_poi_result, poi_content = get_poi_id_no_difficulty(lat=receiver_lat, lng=receiver_lng)
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
        # 'poi_id': 4504135676450865109,
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
        y_predict_c = model_eta_c.predict(x_test)  # 预测
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


@read()
def get_poi_statistic_info_batch(info_list):
    """ poi 的时间，距离等特征"""

    # 1 peak
    poi_id_list = [info['poi_id'] for info in info_list]
    poi_obj_list = ETAPoiStatistics.query \
        .filter(ETAPoiStatistics.poi_id.in_(list(set(poi_id_list)))) \
        .all()
    poi_obj_dict = {
        poi_info.poi_id: poi_info for poi_info in poi_obj_list
    }
    poi_res_list = [
        poi_obj_dict.get(poi_id, None) for poi_id in poi_id_list
    ]

    database_res_list = []
    for info, poi_res in zip(info_list, poi_res_list):
        city_id = info['city_id']
        database_res = None
        if poi_res is not None \
                and city_id == poi_res.city_id:
            database_res = {
                # poi特征
                "percentile_delivery_time_poi": poi_res.percentile_delivery_time_poi,  # 和数据库5.2步骤保持统一命名
                "avg_delivery_time_poi": poi_res.avg_delivery_time_poi,
                "percentile_distance_poi": poi_res.percentile_distance_poi,
                "std_distance_poi": poi_res.std_distance_poi,
                "std_delivery_time_poi": poi_res.std_delivery_time_poi,
                "order_cnt": poi_res.order_cnt,
            }
        database_res_list.append(database_res)

    return database_res_list


def get_eta_c_overhead_v2_batch(search_list):
    """
    eta a段（到店+取货）
    :param search_list: list[dict, dict, ……]
                        transporter_id, receiver_address, receiver_lat, receiver_lng,
                        hour, city_id, weekday,
                        cargo_type_id, cargo_weight
    :return:
    """
    all_result_list = []
    valid_index_list = []  # 记录有效行数的idx
    valid_item_list = []  # 记录有效item，用于inference

    # 0. 兜底结果
    for idx in range(len(search_list)):
        default_poi_time_config = app.config.get('POI_TIME_OVERHEAD_DEFAULT_VALUE_DEFAULT_CITY', {})
        city_poi_time_config_map = app.config.get('POI_TIME_OVERHEAD_DEFAULT_VALUE', {})
        city_poi_time_config = city_poi_time_config_map.get(str(search_list[idx]['city_id']), default_poi_time_config)
        delivery_time = city_poi_time_config.get('receiver_time', 100)

        old_result = [-1, delivery_time]
        all_result_list.append(old_result)  # 一开始先装兜底结果

    # 1. 骑手高峰低谷交付特征数据获取
    # 1.1 查数据库
    search_db_list = [{
        'transporter_id': item['transporter_id'],
        'city_id': item['city_id']}
        for item in search_list]
    try:
        peak_result_list = get_transporter_peak_info_batch(info_list=search_db_list)
    except:
        sentry.captureException()
        return all_result_list

    # 1.2 获取current特征
    for idx, (peak_res, search) in enumerate(zip(peak_result_list, search_list)):
        if peak_res:
            hour = search['hour']
            if (11 <= hour < 13) or (18 <= hour < 20):
                current_cnt_peek = peak_res['cnt_peek1']
                current_per_delivery_time_peek = peak_res['per_delivery_time_peek1']
            elif (9 <= hour < 11) or (15 <= hour < 17) or (20 <= hour < 22):
                current_cnt_peek = peak_res['cnt_peek2']
                current_per_delivery_time_peek = peak_res['per_delivery_time_peek2']
            elif (hour < 9) or (23 <= hour):
                current_cnt_peek = peak_res['cnt_peek3']
                current_per_delivery_time_peek = peak_res['per_delivery_time_peek3']
            else:
                current_cnt_peek = peak_res['cnt_peek0']
                current_per_delivery_time_peek = peak_res['per_delivery_time_peek0']
            peak_res['current_cnt_peek'] = current_cnt_peek
            peak_res['current_per_delivery_time_peek'] = current_per_delivery_time_peek
            valid_index_list.append(idx)  # 把从数据库里能找到的index保存，第一次保存valid_index
    for i in range(len(peak_result_list) - 1, -1, -1):  # 把None删掉
        if peak_result_list[i] is None:
            peak_result_list.pop(i)

    # 2 查询poi相关信息
    # 2.1 调API获得POI信息，查到返回dict，失败返回{}
    address_list = []  # 只查询上一步漏斗通过的search_item
    for valid_idx in valid_index_list:
        item = search_list[valid_idx]
        address_list.append(
            {'lat': item['receiver_lat'],
             'lng': item['receiver_lng'],
             'address': item['receiver_address'],
             }
        )
    try:
        # req_poi_result, poi_content = get_poi_id(lat=receiver_lat, lng=receiver_lng, address=receiver_address)
        poi_content_list = get_poi_id_no_difficulty_batch(address_list=address_list, enable_map=1)  # 有效item(dict)， 无效的是{}
    except:
        sentry.captureException()
        return all_result_list  # TODO any better ways?

    # 2.2 筛选有效poi，更新valid_index_list、peak_result_list
    valid_index_list_tmp = []
    peak_result_list_tmp = []
    search_poi_content_list = []  # db查询
    for i, poi_content in enumerate(poi_content_list):
        receiver_poi_id = poi_content.get("poi_id", 0)
        prob = poi_content.get('prob', 0.0)
        if receiver_poi_id == 0 or prob < 0.5:
            continue
        else:
            search_poi_content_list.append({
                'poi_id': receiver_poi_id,
                'city_id': search_list[valid_index_list[i]]['city_id']}
            )
            valid_index_list_tmp.append(valid_index_list[i])
            peak_result_list_tmp.append(peak_result_list[i])
    valid_index_list = valid_index_list_tmp
    peak_result_list = peak_result_list_tmp
    poi_statistic_list = get_poi_statistic_info_batch(info_list=search_poi_content_list)  # 查不到则item为None

    # 3. 拼接
    valid_index_list_tmp = []
    for idx, peak_item, poi_item in zip(valid_index_list, peak_result_list, poi_statistic_list):
        if poi_item is not None:
            search = {}
            search.update(peak_item)
            search.update(poi_item)
            other_result = {
                'cargo_type_id': str(search_list[idx]['cargo_type_id']),
                'cargo_weight': search_list[idx]['cargo_weight'],
                'hour': str(search_list[idx]['hour']),
                'city_id': str(search_list[idx]['city_id'])
            }
            search.update(other_result)
            valid_index_list_tmp.append(idx)  # 最后有效的id
            valid_item_list.append(search)  # 最终用于做特征工程的特征
    valid_index_list = valid_index_list_tmp

    # 4 inference
    try:
        x_test = feature_extractor_c["dict_vector"].transform(valid_item_list)  # valid_item_list为[] 会抛出ValueError，属于正常流程
        y_predict_c = model_eta_c.predict(x_test)  # 预测 达达接单到到店的时间  shape=(?, )
        y_predict_c = np.expm1(y_predict_c)  # 偏态校正
        for idx, valid_id in enumerate(valid_index_list):
            new_result = [1, y_predict_c[idx]]
            all_result_list[valid_id] = new_result
        return all_result_list
    except:
        sentry.captureException()
        return all_result_list


@read()
def get_transporter_peak_info_batch(info_list):
    """
    从hour_peek那个表找到该骑手的相关信息
    :param info_dict:
    :return:
    """
    # 1 peak
    transporter_id_list = [info['transporter_id'] for info in info_list]
    peak_obj_list = ETATransporterPeekDeliveryInfo.query \
        .filter(ETATransporterPeekDeliveryInfo.transporter_id.in_(list(set(transporter_id_list)))) \
        .all()
    peak_obj_dict = {
        peak_info.transporter_id: peak_info for peak_info in peak_obj_list
    }
    peak_res_list = [
        peak_obj_dict.get(transporter_id, None) for transporter_id in transporter_id_list
    ]

    # 2 transporter
    transporter_info_obj_list = ETATransporterInfo.query \
        .filter(ETATransporterInfo.transporter_id.in_(list(set(transporter_id_list)))) \
        .all()
    transporter_info_obj_dict = {
        transporter_res.transporter_id: transporter_res for transporter_res in transporter_info_obj_list
    }
    transporter_res_list = [
        transporter_info_obj_dict.get(transporter_id, None) for transporter_id in transporter_id_list
    ]

    database_res_list = []
    for info, peak_res, transporter_res in zip(
            info_list, peak_res_list, transporter_res_list):
        city_id = info['city_id']
        database_res = None
        if peak_res is not None and transporter_res is not None \
                and city_id == peak_res.city_id == transporter_res.city_id:
            database_res = {
                # 高峰低谷特征
                # "transporter_id": transporter_peek_res.transporter_id,
                "city_id": peak_res.city_id,
                "delivery_cnt": peak_res.delivery_cnt,
                # "avg_delivery_time1": transporter_peek_res.avg_delivery_time1,
                "avg_delivery_time2": peak_res.avg_delivery_time2,
                # "per_delivery_time1": transporter_peek_res.per_delivery_time1,
                "per_delivery_time2": peak_res.per_delivery_time2,
                "cnt_peek1": peak_res.cnt_peek1,
                "cnt_peek2": peak_res.cnt_peek2,
                "cnt_peek3": peak_res.cnt_peek3,
                "cnt_peek0": peak_res.cnt_peek0,
                "per_delivery_time_peek1": peak_res.per_delivery_time_peek1,
                "per_delivery_time_peek2": peak_res.per_delivery_time_peek2,
                "per_delivery_time_peek3": peak_res.per_delivery_time_peek3,
                "per_delivery_time_peek0": peak_res.per_delivery_time_peek0,

                # A段 骑手特征
                "t_history_order_num": transporter_res.history_order_num,  # 数据库没有前缀t_
                "t_avg_a1_time": transporter_res.avg_a1_time,
                "t_avg_a2_time": transporter_res.avg_a2_time,
            }
        database_res_list.append(database_res)

    return database_res_list


def get_recommend_abtest_id(recommend_id):
    """
    根据待派订单，获取AB测试分组ID
    """
    eta_abtest_group_config = app.config.get('ETA_ABTEST_GROUP_CONFIG', {'blank': 50, 'v1_new_eta': 50})
    default_abtest_id = BLANK_ABTEST_ID

    abtest_id = abtest.get_abtest_id(
        map_id=recommend_id,
        exp_conf=eta_abtest_group_config,
        test_name='eta',
        default=default_abtest_id,
    )
    return abtest_id


def eta_pickup_cut_abtest(test_id_list, param_data_dict_list):
    """
    ETA A 段
    分流
    :param test_id_list:
    :param param_data_dict_list: 入参，list-dict类型
                                      dict: 包含order_id和对应的待派订单
    :return: 两个分流的结果list
    """
    abtest_blank_req_list = []
    abtest_experiment_req_list = []
    res_blank_pickup_time_list = []
    res_experiment_pickup_time_list = []

    # 1. 分流
    for test_id, param_dict in zip(test_id_list, param_data_dict_list):
        if test_id == BLANK_ABTEST_ID:
            abtest_blank_req_list.append(param_dict)

        elif test_id.startswith('v1'):
            abtest_experiment_req_list.append(param_dict)
        else:
            raise RuntimeError()

    # 2. 对照组
    if abtest_blank_req_list:
        res_blank_pickup_time_list = get_pickup_time_overhead_value_list(req_list=abtest_blank_req_list)

    # 3. 实验组
    if abtest_experiment_req_list:
        res_experiment_pickup_time_list = eta_pickup_experiment_flow(order_fastmorse_param_list=abtest_experiment_req_list)
    return abtest_blank_req_list, abtest_experiment_req_list, res_blank_pickup_time_list, res_experiment_pickup_time_list


def eta_receive_cut_abtest(test_id_list, param_data_dict_list):
    """
    ETA C 段
    分流
    :param test_id_list:
    :param param_data_dict_list: 入参，list-dict类型
                                      dict: 包含order_id和对应的待派订单
    :return: 两个分流的结果list
    """
    abtest_blank_req_list = []
    abtest_experiment_req_list = []
    res_blank_receive_time_list = []
    res_experiment_receive_time_list = []

    # 1. 分流
    for test_id, param_dict in zip(test_id_list, param_data_dict_list):
        if test_id == BLANK_ABTEST_ID:
            abtest_blank_req_list.append(param_dict)

        elif test_id.startswith('v1'):
            abtest_experiment_req_list.append(param_dict)
        else:
            raise RuntimeError()

    # 2. 对照组
    if abtest_blank_req_list:
        res_blank_receive_time_list = get_receiver_time_overhead_value_list(req_list=abtest_blank_req_list)

    # 3. 实验组
    if abtest_experiment_req_list:
        res_experiment_receive_time_list = eta_receiver_experiment_flow(order_fastmorse_param_list=abtest_experiment_req_list)
    return abtest_blank_req_list, abtest_experiment_req_list, res_blank_receive_time_list, res_experiment_receive_time_list


def eta_pickup_experiment_flow(order_fastmorse_param_list):
    """
    实验组分流，从feature service获取必要参数

    实验组的入参：search_list: list[dict, dict, ……]
                          transporter_id, transporter_lat, transporter_lng,
                          supplier_id, supplier_lat, supplier_lng,
                          hour, city_id, weekday,
                          cargo_type_id, cargo_weight
    新算法需要的参数：
                        'order_id': order_id,
                        'transporter_id': transporter_id,
                        'transporter_lat': transporter_lat,
                        'transporter_lng': transporter_lng,
                        'supplier_id': supplier_id,
                        'supplier_lat': supplier_lat,
                        'supplier_lng': supplier_lng,
                        'hour': hour,
                        'city_id': city_id,
                        'weekday': weekday,
                        'cargo_type_id': cargo_type_id,
                        'cargo_weight': cargo_weight
    :param order_fastmorse_param_list: 上游fastmorse给的order入参，只有一些基本的字段
    :return:
    """
    # 1. 从别的借口获取order粒度的其他特征（e.g. cargoType）
    order_id_list = [item['orderId'] for item in order_fastmorse_param_list]

    order_info_list = get_order_detail_for_eta_batch(order_id_list=order_id_list)
    order_info_obj_dict = {
        order_info['id']: order_info for order_info in order_info_list
    }
    order_extra_res_list = [
        order_info_obj_dict.get(order_id, None) for order_id in order_id_list
    ]

    # 2. 和上游给的order拼接起来
    order_all_param_list = []  # 汇总所有new ETA需要的参数
    timestamp = time.time()
    for extra_res, fast_order_param in zip(order_extra_res_list, order_fastmorse_param_list):
        hour = pd.Timestamp(timestamp, unit='s', tz='Asia/Shanghai').hour
        weekday = pd.Timestamp(timestamp, unit='s', tz='Asia/Shanghai').dayofweek

        new_param = {
            'transporter_id': fast_order_param.get('transporterId', -1),
            'transporter_lat': fast_order_param.get('transporterLat', -1),
            'transporter_lng': fast_order_param.get('transporterLng', -1),
            'supplier_id': fast_order_param.get('supplierLd', -1),
            'supplier_lat': fast_order_param.get('supplierLat', -1),
            'supplier_lng': fast_order_param.get('supplierLng', -1),
            'city_id': fast_order_param.get('cityId', -1),

            'hour': hour,
            'weekday': weekday,

            'cargo_type_id': extra_res.get('cargoType', 0) if isinstance(extra_res, dict) else 0,
            'cargo_weight': extra_res.get('cargoWeight', 0) if isinstance(extra_res, dict) else 0
        }
        order_all_param_list.append(new_param)
    res_eta_list = get_eta_a_overhead_v2_batch(search_list=order_all_param_list)

    return res_eta_list


def eta_receiver_experiment_flow(order_fastmorse_param_list):
    """
    实验组分流，从feature service获取必要参数

    实验组的入参：search_list: list[dict, dict, ……]
                          transporter_id, transporter_lat, transporter_lng,
                          supplier_id, supplier_lat, supplier_lng,
                          hour, city_id, weekday,
                          cargo_type_id, cargo_weight
    新算法需要的参数：
                        'order_id': order_id,
                        'transporter_id': transporter_id,
                        'transporter_lat': transporter_lat,
                        'transporter_lng': transporter_lng,
                        'supplier_id': supplier_id,
                        'supplier_lat': supplier_lat,
                        'supplier_lng': supplier_lng,
                        'hour': hour,
                        'city_id': city_id,
                        'weekday': weekday,
                        'cargo_type_id': cargo_type_id,
                        'cargo_weight': cargo_weight
    :param order_fastmorse_param_list: 上游fastmorse给的order入参，只有一些基本的字段
    :return:
    """
    # 1. 从别的借口获取order粒度的其他特征（e.g. cargoType）
    order_id_list = [item['orderId'] for item in order_fastmorse_param_list]

    order_info_list = get_order_detail_for_eta_batch(order_id_list=order_id_list)
    order_info_obj_dict = {
        order_info['id']: order_info for order_info in order_info_list
    }
    order_extra_res_list = [
        order_info_obj_dict.get(order_id, None) for order_id in order_id_list
    ]

    # 2. 和上游给的order拼接起来
    order_all_param_list = []  # 汇总所有new ETA需要的参数
    timestamp = time.time()
    for extra_res, fast_order_param in zip(order_extra_res_list, order_fastmorse_param_list):
        hour = pd.Timestamp(timestamp, unit='s', tz='Asia/Shanghai').hour
        weekday = pd.Timestamp(timestamp, unit='s', tz='Asia/Shanghai').dayofweek

        new_param = {
            'transporter_id': fast_order_param.get('transporterId', -1),
            'receiver_lat': fast_order_param.get('receiverLat', 0),
            'receiver_lng': fast_order_param.get('receiverLng', 0),
            'city_id': fast_order_param.get('cityId', -1),

            'hour': hour,
            'weekday': weekday,

            'cargo_type_id': extra_res.get('cargoType', 0) if isinstance(extra_res, dict) else 0,
            'cargo_weight': extra_res.get('cargoWeight', 0) if isinstance(extra_res, dict) else 0,
            'receiver_address': extra_res.get('receiverAddress', -1) if isinstance(extra_res, dict) else 0
        }
        order_all_param_list.append(new_param)
    res_eta_list = get_eta_c_overhead_v2_batch(search_list=order_all_param_list)

    return res_eta_list


def is_new_eta_call(param_list_dict, flag='recOrderId'):
    """
    判断是否是fastmores的新参数调用
    """
    default = -999
    if len(param_list_dict) <= 0:
        return False

    # 1. 拿出batch的第一个
    param = param_list_dict[0]
    recom_order_id = param.get(flag, default)
    if recom_order_id == default:
        return False
    return True
