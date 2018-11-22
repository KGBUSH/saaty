#! /usr/bin/python
#  -*- coding: utf-8 -*-


import time
import datetime
from core import app
from core import kafkaBizLogger
from core import algoKafkaLogger
from saaty.constants import kafka_event
from saaty.utils.abtest import get_order_ab_test_flag
from saaty.utils.config_detail import get_dynamic_pickup_arrive_config_detail
from saaty.utils.order_category import get_order_category
from saaty.services.poi_time_latency import get_poi_latency_difficulty
from saaty.services.poi_time_latency import get_latency_delta


def get_exclusive_assign_latency_result(city_id, order_id, supplier_id, supplier_lng, supplier_lat,
                                        receiver_lng, receiver_lat,
                                        original_pickup_latency, original_arrive_latency, label_ids):
    start_time = time.time()

    # 待返回的变量初始化
    pickup_latency_ratio = 0.0
    pickup_latency_delta = 0
    arrive_latency_ratio = 0.0
    arrive_latency_delta = 0

    # 中间变量
    is_pickup_latency_changed = 0
    is_arrive_latency_changed = 0
    order_category = get_order_category(label_ids)

    # 专享订单开启城市列表
    enable_city_list = app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_EXCLUSIVE_ASSIGN_CITY_ENABLE_LIST", [])
    if city_id in enable_city_list:
        pickup_latency_ratio = 600/original_pickup_latency if original_pickup_latency > 0 else 0.0
        pickup_latency_delta = 600
        arrive_latency_ratio = 600/original_arrive_latency if original_arrive_latency > 0 else 0.0
        arrive_latency_delta = 600

    end_time = time.time()
    # DYNAMIC_POI_TIME_EVENT = 10386 日志
    exclusive_info = {
        "is_exclusive_assign": 1,
        "order_id": order_id,
        "label_ids": label_ids,
        "order_category": order_category,
        "city_id": city_id,
        "original_pickup_latency": original_pickup_latency,
        "original_arrive_latency": original_arrive_latency,
        "supplier_id": supplier_id,
        "supplier_lng": supplier_lng,
        "supplier_lat": supplier_lat,
        "receiver_lng": receiver_lng,
        "receiver_lat": receiver_lat,
        "dynamic_pickup_latency_ratio": arrive_latency_ratio,
        "dynamic_arrive_latency_ratio": arrive_latency_ratio,
        "dynamic_pickup_latency_delta": pickup_latency_delta,
        "dynamic_arrive_latency_delta": arrive_latency_delta,
        "now_timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "is_pickup_latency_changed": is_pickup_latency_changed,
        "is_arrive_latency_changed": is_arrive_latency_changed,
        "start_time": start_time,
        "end_time": end_time,
        "time_used": round(end_time - start_time, 3)
    }
    # kafkaBizLogger.info(kafka_event.DYNAMIC_POI_TIME_EVENT, exclusive_info)
    algoKafkaLogger.info(kafka_event.DYNAMIC_POI_TIME_EVENT, exclusive_info)

    return pickup_latency_ratio, pickup_latency_delta, arrive_latency_ratio, arrive_latency_delta


def get_vip_assign_latency_result(city_id, order_id, supplier_id, supplier_lng, supplier_lat,
                                  receiver_lng, receiver_lat,
                                  original_pickup_latency, original_arrive_latency, label_ids):
    start_time = time.time()

    # 待返回的变量初始化
    pickup_latency_ratio = 0.0
    pickup_latency_delta = 0
    arrive_latency_ratio = 0.0
    arrive_latency_delta = 0

    # 中间变量
    is_pickup_latency_changed = 0
    is_arrive_latency_changed = 0
    order_category = get_order_category(label_ids)
    supplier_time_difficulty = 0.0
    receiver_time_difficulty = 0.0
    is_vip_latency_service_open = 0
    ab_test_flag = 'con_100_100_m1'
    control_flag = 1
    pickup_latency_config_group = 100
    arrive_latency_config_group = 100
    pickup_param_group = {
        'schema': [0, 0, 0, 0, 0, 0, 0.1, 0.1, 0.1, 0.1],
        'threshold': 0.7
    }
    arrive_param_group = {
        'schema': [0, 0, 0, 0, 0, 0, 0.1, 0.1, 0.1, 0.1],
        'threshold': 0.7
    }
    get_difficulty_method = 'm1'

    # 获取城市激活列表
    enable_city_list = app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_CITY_ENABLE_LIST", [])
    if city_id in enable_city_list:
        # 获取AB测试分组
        city_group = 'DYNAMIC_PICKUP_ARRIVE_LATENCY_CITY_AB_TEST'
        test_name = 'dynamic_pickup_arrive'
        ab_test_flag = get_order_ab_test_flag(order_id, city_id, city_group, test_name)

        control_flag, pickup_latency_config_group, arrive_latency_config_group, get_difficulty_method = \
            get_dynamic_pickup_arrive_config_detail(ab_test_flag)

        supplier_time_difficulty, receiver_time_difficulty = get_poi_latency_difficulty(city_id,
                                                                                        supplier_id,
                                                                                        supplier_lng,
                                                                                        supplier_lat,
                                                                                        receiver_lng,
                                                                                        receiver_lat,
                                                                                        get_difficulty_method)

        # 获取到店时效、送达时效策略分组
        latency_schema_group = app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_SCHEMA_GROUP", {})
        pickup_param_group = latency_schema_group.get(pickup_latency_config_group, {})
        arrive_param_group = latency_schema_group.get(arrive_latency_config_group, {})

        if latency_schema_group:
            if supplier_time_difficulty >= pickup_param_group.get("threshold", 0):
                pickup_latency_ratio = pickup_param_group["schema"][int(10 * supplier_time_difficulty)]
                is_pickup_latency_changed = 1

            arrive_latency_ratio = 0.0
            is_arrive_latency_changed = 0

        # 将比例转化为固定的时间延迟
        latency_step = 300
        min_pickup_latency_delta = app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_MIN_LATENCY_DELTA", 300)
        max_pickup_latency_delta = min(app.config.get("DYNAMIC_PICKUP_ARRIVE_LATENCY_MAX_LATENCY_DELTA", 1200),
                                       original_arrive_latency - original_pickup_latency)
        if max_pickup_latency_delta > min_pickup_latency_delta:
            pickup_latency_delta = get_latency_delta(original_pickup_latency,
                                                     pickup_latency_ratio,
                                                     latency_step,
                                                     min_pickup_latency_delta,
                                                     max_pickup_latency_delta)
        else:
            pickup_latency_delta = 0

        arrive_latency_delta = 0

    end_time = time.time()
    # DYNAMIC_POI_TIME_EVENT = 10386 日志
    vip_info = {
        "vip_assign_flag": 1,
        "is_vip_latency_service_open": is_vip_latency_service_open,
        "order_id": order_id,
        "label_ids": label_ids,
        "order_category": order_category,
        "city_id": city_id,
        "original_pickup_latency": original_pickup_latency,
        "original_arrive_latency": original_arrive_latency,
        "supplier_id": supplier_id,
        "supplier_lng": supplier_lng,
        "supplier_lat": supplier_lat,
        "receiver_lng": receiver_lng,
        "receiver_lat": receiver_lat,
        "dynamic_pickup_latency_ratio": arrive_latency_ratio,
        "dynamic_arrive_latency_ratio": arrive_latency_ratio,
        "dynamic_pickup_latency_delta": pickup_latency_delta,
        "dynamic_arrive_latency_delta": arrive_latency_delta,
        "ab_test_flag": ab_test_flag,
        "control_flag": control_flag,
        "pickup_latency_config_group": pickup_latency_config_group,
        "arrive_latency_config_group": arrive_latency_config_group,
        "pickup_param_group": pickup_param_group,
        "arrive_param_group": arrive_param_group,
        "get_difficulty_method": get_difficulty_method,
        "supplier_time_difficulty": supplier_time_difficulty,
        "receiver_time_difficulty": receiver_time_difficulty,
        "now_timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "is_pickup_latency_changed": is_pickup_latency_changed,
        "is_arrive_latency_changed": is_arrive_latency_changed,
        "start_time": start_time,
        "end_time": end_time,
        "time_used": round(end_time - start_time, 3)
    }
    # kafkaBizLogger.info(kafka_event.DYNAMIC_POI_TIME_EVENT, vip_info)
    algoKafkaLogger.info(kafka_event.DYNAMIC_POI_TIME_EVENT, vip_info)

    return pickup_latency_ratio, pickup_latency_delta, arrive_latency_ratio, arrive_latency_delta


if __name__ == "__main__":
    pass
