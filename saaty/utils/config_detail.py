# -*- coding: utf-8 -*-


def get_config_detail(ab_test_flag):
    items = ab_test_flag.strip().split('_')

    control_flag = 1 if items[0] == 'con' else 0
    latency_config_group = int(items[1])

    get_difficulty_method = 'm1'

    if len(items) > 2:
        try:
            get_difficulty_method = str(items[2])
        except:
            pass

    return control_flag, latency_config_group, get_difficulty_method


def get_dynamic_pickup_arrive_config_detail(ab_test_flag):
    items = ab_test_flag.strip().split('_')

    control_flag = 1 if items[0] == 'con' else 0
    pickup_latency_config_group = int(items[1])
    arrive_latency_config_group = int(items[2])
    get_difficulty_method = str(items[3])

    return control_flag, pickup_latency_config_group, arrive_latency_config_group, get_difficulty_method

