#!/usr/bin/python
# -*- coding:utf-8 -*-
#
# Copyright (C) 2018 LIU Yiming <liuyiming@imdada.cn>


import os
import datetime
import time
import geohash
from core import app
from core import cache
from core import sentry
from common.metric.metric_util import inc as metric_inc
from saaty.utils.utils import load_object, normalize, get_feedback_city_poi_list
from saaty.constants import cache_keys, cache_expire, metric_constants
from saaty.models.poi_time_difficulty import POIReceiverTimeDifficulty
from saaty.models.poi_time_difficulty import POISupplierTimeDifficulty, \
    GeohashArtificialDifficultAddress
from saaty.utils.order_category import get_order_category
from saaty.utils.address_floor import BuildingRecognizer
from saaty.services.rpc_services.delivery_center_rpc_service import \
    get_order_detail_single
from saaty.services.rpc_services.hubble_poi_rpc_service import get_poi_id
from core import algoKafkaLogger

from saaty.constants import kafka_event
from saaty.utils.abtest import get_order_ab_test_flag
from saaty.utils.config_detail import get_config_detail

__all__ = [
    'get_poi_latency_view_result'
]

# 初始化LR权重模型映射文件
PROJECT_PATH = os.path.abspath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir))

# 骑士反馈问题receiver_poi
courier_feedback_poi_dict = load_object(
    PROJECT_PATH + "/resource_data/courier_feedback_receiver_8_geohash.pkl")

# 城市站反馈问题receiver_poi
FEEDBACK_CITY_LIST = app.config.get('FEEDBACK_CITY_LIST', [])
FEEDBACK_CITY_POI_NAME_ID_DICT = app.config.get("FEEDBACK_CITY_POI_IDS", {})
FEEDBACK_CITY_POI_DICT = get_feedback_city_poi_list(
    FEEDBACK_CITY_POI_NAME_ID_DICT)
FEEDBACK_CITY_SUPPLIER_ID_DICT = app.config.get("FEEDBACK_CITY_SUPPLIER_IDS",
                                                {})

# M2模型专用
supplier_id_weight_dict = load_object(
    PROJECT_PATH + "/resource_data/supplier_id_weight_dict.0.pkl")
receiver_geohash_weight_dict = load_object(
    PROJECT_PATH + "/resource_data/receiver_geohash_weight_dict.0.pkl")

# M3模型专用
supplier_id_m3_dict = load_object(
    PROJECT_PATH + "/resource_data/supplier_id_m3_dict.0.pkl")
receiver_geohash_m3_dict = load_object(
    PROJECT_PATH + "/resource_data/receiver_geohash_m3_dict.0.pkl")


def get_artificial_poi_latency_info(city_id, order_id, label_ids, receiver_lat,
                                    receiver_lng, original_latency,
                                    heavy_weather_latency):
    """
    缓存与数据库收录，geohash 级别判断，按比例延时
    :param city_id:
    :param order_id:
    :param label_ids:
    :param receiver_lat:
    :param receiver_lng:
    :return:
    """
    # 待返回变量
    success = False
    dynamic_latency_ratio = 0.0
    dynamic_latency_delta = 0
    if not app.config.get("ARTIFICIAL_POI_LATENCY_SWITCH", 0):
        return success, dynamic_latency_ratio, dynamic_latency_delta

    receiver_geohash = geohash.encode(float(receiver_lat), float(receiver_lng), 8)
    geohash_diff_ratio = read_artificial_address_geohash_difficulty_ratio(
        geohash_info=receiver_geohash)
    if geohash_diff_ratio > 0.0:
        dynamic_latency_ratio = geohash_diff_ratio
        success = True
        # 计算具体的延时长度
        latency_step = 300
        min_latency_delta = 0
        max_latency_delta = app.config.get("POI_LATENCY_MAX_LATENCY_DELTA",
                                           2400)
        is_heavy_weather_latency_longer = 0

        dynamic_latency_delta = get_latency_delta(original_latency,
                                                  dynamic_latency_ratio,
                                                  latency_step,
                                                  min_latency_delta,
                                                  max_latency_delta)

        heavy_weather_latency_ratio = round(
            float(heavy_weather_latency) / (original_latency + 0.001), 3)

        # 如果恶劣天气延时长度大于0，则根据恶劣天气延时长度对困难poi延时长度进行调整
        if heavy_weather_latency > 0.0:
            is_heavy_weather_latency_longer = 1 if heavy_weather_latency >= dynamic_latency_delta else 0
            if is_heavy_weather_latency_longer:
                # 如果运营的雨天延时较长的话，saaty不再重复延时
                dynamic_latency_ratio = 0.0
                dynamic_latency_delta = 0
            else:
                # 如果运营的雨天延时较短，最终的延时长度为saaty计算出来的延时
                dynamic_latency_delta = dynamic_latency_delta - heavy_weather_latency
                dynamic_latency_ratio = round(float(dynamic_latency_delta) /
                                              original_latency, 3) if original_latency > 0 else 0
        info = {
            "comment": u"人工地址geohash动态延时",
            "order_id": order_id,
            "label_ids": label_ids,
            "city_id": city_id,
            "original_latency": original_latency,
            "heavy_weather_latency": heavy_weather_latency,
            "heavy_weather_latency_ratio": heavy_weather_latency_ratio,
            "is_heavy_weather_latency_longer": is_heavy_weather_latency_longer,
            "receiver_lng": receiver_lng,
            "receiver_lat": receiver_lat,
            "dynamic_latency_ratio": dynamic_latency_ratio,
            "dynamic_latency_delta": dynamic_latency_delta
        }
        algoKafkaLogger.info(kafka_event.DYNAMIC_POI_TIME_EVENT, info)

    return success, dynamic_latency_ratio, dynamic_latency_delta


def get_poi_latency_view_result(city_id, supplier_id, supplier_lat,
                                supplier_lng, receiver_lat, receiver_lng,
                                **kwargs):
    """
    获取困难POI按倍数延长时效结果

    :param city_id:
    :param supplier_id:
    :param supplier_lat:
    :param supplier_lng:
    :param receiver_lat:
    :param receiver_lng:
    :param kwargs:
    :return:
    """
    start_time = time.time()
    # kwargs
    order_id = kwargs.get('order_id', '')
    label_ids = kwargs.get('label_ids')
    original_latency = kwargs.get('original_latency', 0)
    heavy_weather_latency = kwargs.get('heavy_weather_latency', 0)

    # 待返回变量
    dynamic_latency_ratio = 0.0
    dynamic_latency_delta = 0

    # 中间变量初始化(记日志)
    is_latency_changed = 0
    ab_test_flag = 'con_101_m1'
    control_flag = 1
    latency_config_group = 101
    param_group = {
        'schema': [0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.3, 0.4],
        'threshold': 0.7,
        'alpha_1': 0.5,
        'alpha_2': 0.5
    }
    latency_score = 0.0
    get_difficulty_method = 'm1'
    is_courier_feedback_poi = 0
    is_city_station_feedback_poi = 0
    is_city_station_feedback_supplier_id = 0
    supplier_time_difficulty = 0.0
    receiver_time_difficulty = 0.0
    receiver_poi_difficulty_hubble = 0.0
    is_service_open = 0
    is_heavy_weather_latency = 1 if heavy_weather_latency > 0 else 0
    heavy_weather_latency_ratio = 0.0  # 恶劣天气延时倍数
    is_heavy_weather_latency_longer = 0
    order_category = get_order_category(label_ids)
    order_detail_info = u''
    cargo_type = 0
    distance = 0
    block_id = 0
    area_id = 0
    supplier_address = u''
    receiver_address = u''
    receiver_poi_id = u''
    map_id = u''
    supplier_floor = 0
    receiver_floor = 0

    # 调用Delivery-Center获取地址字符串
    if order_id:
        send_result, order_detail_info = get_order_detail_single(order_id)
        if send_result:
            cargo_type = int(order_detail_info.get("cargoType", 0))
            distance = int(order_detail_info.get("distance", 0))
            block_id = int(order_detail_info.get("blockId", 0))
            area_id = int(order_detail_info.get("areaId", 0))
            supplier_address = order_detail_info.get("supplierAddress",
                                                     u"未填写地址")
            receiver_address = order_detail_info.get("receiverAddress",
                                                     u"未填写地址")

            try:
                supplier_build = BuildingRecognizer()
                supplier_floor = supplier_build.get_building_floor(
                    supplier_address)
                receiver_build = BuildingRecognizer()
                receiver_floor = receiver_build.get_building_floor(
                    receiver_address)
            except:
                pass

    # 调用Hubble获取收货地POI
    if receiver_lat and receiver_lng:
        req_poi_result, poi_content = get_poi_id(receiver_lat, receiver_lng,
                                                 receiver_address)
        if req_poi_result:
            receiver_poi_id = poi_content.get("poi_id", 0)
            receiver_poi_difficulty_hubble = poi_content.get('poi_difficulty',
                                                             0.0)

    is_service_open = 1
    try:
        # 获取城市激活列表
        enable_city_list = app.config.get("POI_LATENCY_CITY_ENABLE_LIST", [])

        if city_id in enable_city_list:
            # 获取AB测试分组
            city_group = 'POI_LATENCY_CITY_AB_TEST'
            test_name = 'saaty_order'
            map_id = str(supplier_id) + str(receiver_poi_id)
            ab_test_flag = get_order_ab_test_flag(map_id, city_id, city_group,
                                                  test_name)

            control_flag, latency_config_group, get_difficulty_method = get_config_detail(
                ab_test_flag)

            supplier_time_difficulty, receiver_time_difficulty = get_poi_latency_difficulty(
                city_id,
                supplier_id,
                supplier_lng,
                supplier_lat,
                receiver_lng,
                receiver_lat,
                get_difficulty_method)

            # 获取策略分组
            latency_schema_group = app.config.get("POI_LATENCY_SCHEMA_GROUP",
                                                  {})
            param_group = latency_schema_group.get(latency_config_group, {})

            alpha_1 = param_group.get("alpha_1", 0.5)
            alpha_2 = param_group.get("alpha_2", 0.5)
            latency_score = get_poi_latency_score(alpha_1,
                                                  alpha_2,
                                                  supplier_time_difficulty,
                                                  receiver_poi_difficulty_hubble)

            # 骑士、城市站反馈的问题poi优先计算延时倍数，其他的订单根据配送难度获取延时倍数
            is_courier_feedback_poi = courier_feedback_poi(receiver_lng,
                                                           receiver_lat)
            is_city_station_feedback_poi = city_station_feedback_poi(city_id,
                                                                     receiver_poi_id)
            is_city_station_feedback_supplier_id = city_station_feedback_supplier_id(
                city_id, supplier_id)
            if is_courier_feedback_poi or is_city_station_feedback_poi or is_city_station_feedback_supplier_id:
                dynamic_latency_ratio = app.config.get(
                    "POI_LATENCY_RATIO_COURIER_FEEDBACK", 0.3)
                is_latency_changed = 1
            elif latency_schema_group:
                if latency_score >= param_group.get("threshold", 0):
                    dynamic_latency_ratio = param_group["schema"][
                        int(10 * latency_score)]
                    is_latency_changed = 1

            # 如果原始时效大于0，则根据延时ratio计算具体的延时长度
            if original_latency > 0:
                # 将比例转化为固定的时间延迟
                latency_step = 300
                min_latency_delta = 0
                max_latency_delta = app.config.get(
                    "POI_LATENCY_MAX_LATENCY_DELTA", 2400)
                # 计算具体的延时长度
                dynamic_latency_delta = get_latency_delta(original_latency,
                                                          dynamic_latency_ratio,
                                                          latency_step,
                                                          min_latency_delta,
                                                          max_latency_delta)

                heavy_weather_latency_ratio = round(
                    float(heavy_weather_latency) / original_latency, 3)

                # 如果恶劣天气延时长度大于0，则根据恶劣天气延时长度对困难poi延时长度进行调整
                if heavy_weather_latency > 0:
                    is_heavy_weather_latency_longer = 1 if heavy_weather_latency >= dynamic_latency_delta else 0
                    if is_heavy_weather_latency_longer:
                        # 如果运营的雨天延时较长的话，saaty不再重复延时
                        dynamic_latency_ratio = 0.0
                        dynamic_latency_delta = 0
                    else:
                        # 如果运营的雨天延时较短，最终的延时长度为saaty计算出来的延时
                        dynamic_latency_delta = dynamic_latency_delta - heavy_weather_latency
                        dynamic_latency_ratio = round(
                            float(dynamic_latency_delta) / original_latency,
                            3) if original_latency > 0 else 0
    except:
        sentry.captureException()

    end_time = time.time()

    info = {
        "is_service_open": is_service_open,
        "comment": u"困难poi动态延时",
        "order_id": order_id,
        "label_ids": label_ids,
        "order_category": order_category,
        "city_id": city_id,
        "original_latency": original_latency,
        "is_heavy_weather_latency": is_heavy_weather_latency,
        "heavy_weather_latency": heavy_weather_latency,
        "heavy_weather_latency_ratio": heavy_weather_latency_ratio,
        "is_heavy_weather_latency_longer": is_heavy_weather_latency_longer,
        "supplier_id": supplier_id,
        "supplier_lng": supplier_lng,
        "supplier_lat": supplier_lat,
        "receiver_lng": receiver_lng,
        "receiver_lat": receiver_lat,
        "receiver_poi_id": receiver_poi_id,
        "dynamic_latency_ratio": dynamic_latency_ratio,
        "dynamic_latency_delta": dynamic_latency_delta,
        "ab_test_flag": ab_test_flag,
        "control_flag": control_flag,
        "latency_config_group": latency_config_group,
        "param_group": param_group,
        "get_difficulty_method": get_difficulty_method,
        "is_courier_feedback_poi": is_courier_feedback_poi,
        "is_city_station_feedback_poi": is_city_station_feedback_poi,
        "is_city_station_feedback_supplier_id": is_city_station_feedback_supplier_id,
        "latency_score": latency_score,
        "supplier_time_difficulty": supplier_time_difficulty,
        "receiver_time_difficulty": receiver_time_difficulty,
        "receiver_poi_difficulty_hubble": receiver_poi_difficulty_hubble,
        "now_timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "is_latency_changed": is_latency_changed,
        "order_detail_info": order_detail_info,
        "supplier_address": supplier_address,
        "supplier_floor": supplier_floor,
        "receiver_address": receiver_address,
        "receiver_floor": receiver_floor,
        "cargo_type": cargo_type,
        "distance": distance,
        "block_id": block_id,
        "area_id": area_id,
        "time_used": round(end_time - start_time, 3)
    }
    # DYNAMIC_POI_TIME_EVENT = 10386
    algoKafkaLogger.info(kafka_event.DYNAMIC_POI_TIME_EVENT, info)

    # 对照组实际不延时
    if 1 == control_flag:
        dynamic_latency_ratio = 0.0
        dynamic_latency_delta = 0

    # monitor 新版监控
    # 查看日志 group by city_id, order_category
    metric_tags = {
        'city_id': city_id,
        'order_category': order_category
    }
    # 统计总的请求order_id量
    key_order_cnt = metric_constants.METRIC_SAATY_DYNAMIC_LATENCY.format(
        type="order_cnt")
    metric_inc(key_order_cnt, 1, metric_tags)
    # 统计总的触发延时的order_id量
    if dynamic_latency_delta > 0:
        key_latency_order_cnt = metric_constants.METRIC_SAATY_DYNAMIC_LATENCY.format(
            type="latency_order_cnt")
        metric_inc(key_latency_order_cnt, 1, metric_tags)
    # 统计总的原始时效
    key_original_latency_sum = metric_constants.METRIC_SAATY_DYNAMIC_LATENCY.format(
        type="original_latency_sum")
    metric_inc(key_original_latency_sum, original_latency, metric_tags)
    # 统计总的原始恶劣天气延时
    key_heavy_weather_latency_sum = metric_constants.METRIC_SAATY_DYNAMIC_LATENCY.format(
        type="heavy_weather_latency_sum")
    metric_inc(key_heavy_weather_latency_sum, heavy_weather_latency,
               metric_tags)
    # 统计总的延时倍数
    key_latency_ratio_sum = metric_constants.METRIC_SAATY_DYNAMIC_LATENCY.format(
        type="latency_ratio_sum")
    metric_inc(key_latency_ratio_sum, dynamic_latency_ratio, metric_tags)

    return max(dynamic_latency_ratio, 0.0), max(dynamic_latency_delta, 0)


def courier_feedback_poi(receiver_lng, receiver_lat):
    receiver_geohash = geohash.encode(float(receiver_lat), float(receiver_lng),
                                      8)
    occur_num = courier_feedback_poi_dict.get(str(receiver_geohash), 0)
    is_courier_feedback_poi = 1 if occur_num >= 1 else 0

    return is_courier_feedback_poi


def city_station_feedback_poi(city_id, poi_id):
    is_city_station_feedback_poi = 0
    if city_id in FEEDBACK_CITY_LIST:
        if poi_id in FEEDBACK_CITY_POI_DICT.get(city_id, []):
            is_city_station_feedback_poi = 1
    return is_city_station_feedback_poi


def city_station_feedback_supplier_id(city_id, supplier_id):
    is_city_station_feedback_supplier_id = 0
    if city_id in FEEDBACK_CITY_LIST:
        if str(supplier_id) in FEEDBACK_CITY_SUPPLIER_ID_DICT.get(city_id, []):
            is_city_station_feedback_supplier_id = 1
    return is_city_station_feedback_supplier_id


def get_poi_latency_difficulty(city_id, supplier_id, supplier_lng, supplier_lat,
                               receiver_lng, receiver_lat,
                               get_difficulty_method):
    supplier_time_difficulty = 0.0
    receiver_time_difficulty = 0.0

    if get_difficulty_method == 'm1':
        # 获取延迟时效
        supplier_time_difficulty, receiver_time_difficulty = get_poi_latency_difficulty_m1(
            city_id,
            supplier_id,
            supplier_lng,
            supplier_lat,
            receiver_lng,
            receiver_lat)
    elif get_difficulty_method == 'm2':
        supplier_time_difficulty, receiver_time_difficulty = get_poi_latency_difficulty_m2(
            supplier_id,
            receiver_lng,
            receiver_lat)
    elif get_difficulty_method == 'm3':
        supplier_time_difficulty, receiver_time_difficulty = get_poi_latency_difficulty_m3(
            city_id,
            supplier_id,
            receiver_lng,
            receiver_lat)

    return supplier_time_difficulty, receiver_time_difficulty


def read_artificial_address_geohash_difficulty_ratio(geohash_info):
    geohash_difficult_ratio = 0.0
    # 从缓存获取
    geohash_cache_key = cache_keys.CACHE_KEY_ARTIFICIAL_GEOHASH_KEY.format(
        geohash_info=geohash_info
    )
    geohash_diff_info = cache.get(geohash_cache_key)

    if geohash_diff_info is not None:
        geohash_difficult_ratio = geohash_diff_info
    else:
        # 从数据库获取
        geohash_result = GeohashArtificialDifficultAddress.query \
            .filter(GeohashArtificialDifficultAddress.is_del == 0,
                    GeohashArtificialDifficultAddress.geohash == geohash_info) \
            .first()
        if geohash_result:
            geohash_difficult_ratio = app.config.get(
                "ARTIFICIAL_ADDRESS_GEOHASH_DIFFICULTY_RATIO", 0.0)

        cache.set(geohash_cache_key, geohash_difficult_ratio,
                  cache_expire.CHCHE_EXPIRE_TIME_MIDDLE)

    return geohash_difficult_ratio


def read_supplier_time_difficulty(city_id, supplier_id, supplier_lng,
                                  supplier_lat):
    """
    获取商户取货难度系数，优先使用cache数据

    :param city_id:
    :param supplier_id:
    :param supplier_lng:
    :param supplier_lat:
    :return:
    """
    supplier_time_difficulty = 0.0

    # 从缓存获取
    supplier_cache_key = cache_keys.SUPPLIER_TIME_DIFFICULTY.format(
        supplier_id=supplier_id, supplier_lng=supplier_lng,
        supplier_lat=supplier_lat, city_id=city_id,
    )
    supplier_time_cache = cache.get(supplier_cache_key)

    if supplier_time_cache is not None:
        supplier_time_difficulty = supplier_time_cache
    else:
        # 从数据库获取
        supplier_result = POISupplierTimeDifficulty.query \
            .filter(POISupplierTimeDifficulty.supplier_id == supplier_id,
                    POISupplierTimeDifficulty.supplier_lng == supplier_lng,
                    POISupplierTimeDifficulty.supplier_lat == supplier_lat,
                    POISupplierTimeDifficulty.city_id == city_id) \
            .first()
        if supplier_result:
            supplier_time_difficulty = supplier_result.poi_value

        cache.set(supplier_cache_key, supplier_time_difficulty,
                  cache_expire.CHCHE_EXPIRE_TIME_LONG)

    return supplier_time_difficulty


def read_poi_receiver_time_difficulty(city_id, receiver_lng, receiver_lat):
    """
    获取POI维度送达时间难度系数，优先使用缓存数据

    :param city_id:
    :param receiver_lng:
    :param receiver_lat:
    :return:
    """
    receiver_time_difficulty = 0.0

    # 从缓存中获取
    receiver_cache_key = cache_keys.RECEIVER_TIME_DIFFICULTY.format(
        receiver_lng=receiver_lng, receiver_lat=receiver_lat, city_id=city_id,
    )
    receiver_time_cache = cache.get(receiver_cache_key)

    if receiver_time_cache is not None:
        receiver_time_difficulty = receiver_time_cache
    else:
        # 从数据库获取
        receiver_result = POIReceiverTimeDifficulty.query \
            .filter(POIReceiverTimeDifficulty.receiver_lng == receiver_lng,
                    POIReceiverTimeDifficulty.receiver_lat == receiver_lat,
                    POIReceiverTimeDifficulty.city_id == city_id) \
            .first()

        if receiver_result:
            receiver_time_difficulty = receiver_result.poi_value

        cache.set(receiver_cache_key, receiver_time_difficulty,
                  cache_expire.CHCHE_EXPIRE_TIME_LONG)

    return receiver_time_difficulty


def get_poi_latency_difficulty_m1(city_id, supplier_id, supplier_lng,
                                  supplier_lat, receiver_lng, receiver_lat):
    """
    获取取货难度系数，送达难度系数

    :param city_id:
    :param supplier_id:
    :param supplier_lng:
    :param supplier_lat:
    :param receiver_lng:
    :param receiver_lat:
    :return:
    """
    supplier_time_difficulty = read_supplier_time_difficulty(
        city_id=city_id,
        supplier_id=supplier_id,
        supplier_lng=supplier_lng,
        supplier_lat=supplier_lat
    )

    receiver_time_difficulty = read_poi_receiver_time_difficulty(
        city_id=city_id,
        receiver_lat=receiver_lat,
        receiver_lng=receiver_lng
    )

    return supplier_time_difficulty, receiver_time_difficulty


def get_poi_latency_difficulty_m2(supplier_id, receiver_lng, receiver_lat):
    """
    获取取货难度系数，送达难度系数

    :param supplier_id:
    :param receiver_lng:
    :param receiver_lat:
    :return:
    """
    supplier_id_weight = supplier_id_weight_dict.get(str(supplier_id), 0)
    supplier_weight_min = -4.0
    supplier_weight_max = 4.0
    supplier_time_difficulty = 1.0 - normalize(supplier_id_weight,
                                               supplier_weight_min,
                                               supplier_weight_max)

    receiver_geohash = geohash.encode(float(receiver_lat), float(receiver_lng),
                                      7)
    receiver_geohash_weight = receiver_geohash_weight_dict.get(
        str(receiver_geohash), 0)
    receiver_weight_min = -4.0
    receiver_weight_max = 4.0
    receiver_time_difficulty = 1.0 - normalize(receiver_geohash_weight,
                                               receiver_weight_min,
                                               receiver_weight_max)

    return supplier_time_difficulty, receiver_time_difficulty


def get_poi_latency_difficulty_m3(city_id, supplier_id, receiver_lng,
                                  receiver_lat):
    """
    获取取货难度系数，送达难度系数

    :param city_id:
    :param supplier_id:
    :param receiver_lng:
    :param receiver_lat:
    :return:
    """
    supplier_time_difficulty = supplier_id_m3_dict.get(int(city_id), {}).get(
        int(supplier_id), 0)
    receiver_geohash = geohash.encode(float(receiver_lat), float(receiver_lng),
                                      7)
    receiver_time_difficulty = receiver_geohash_m3_dict.get(int(city_id),
                                                            {}).get(
        str(receiver_geohash), 0)

    return supplier_time_difficulty, receiver_time_difficulty


def get_poi_latency_score(alpha_1, alpha_2, supplier_time_difficulty,
                          receiver_time_difficulty):
    # 计算难度系数
    latency_score = 0.0

    if alpha_1 > 0 and (alpha_1 + alpha_2 - 1.0) < 0.0001:
        latency_score = alpha_1 * supplier_time_difficulty + alpha_2 * receiver_time_difficulty

    latency_score = max(min(latency_score, 1.0), 0.0)

    return latency_score


def get_latency_delta(original_latency, dynamic_latency_ratio, latency_step=300,
                      min_latency_delta=0,
                      max_latency_delta=2400):
    dynamic_latency_delta = round(
        (original_latency * dynamic_latency_ratio) / int(latency_step)) \
                            * int(latency_step)

    if dynamic_latency_delta <= min_latency_delta:
        dynamic_latency_delta = min_latency_delta
    elif dynamic_latency_delta >= max_latency_delta:
        dynamic_latency_delta = max_latency_delta

    return dynamic_latency_delta


if __name__ == "__main__":
    # city_id = 1
    # poi_id = u'10412611807490621560'
    # is_city_station_feedback_poi = city_station_feedback_poi(city_id, poi_id)
    # print 'is_city_station_feedback_poi : ', is_city_station_feedback_poi
    #
    pass
