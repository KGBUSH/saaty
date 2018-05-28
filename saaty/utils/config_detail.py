# -*- coding: utf-8 -*-


def get_config_detail(ab_test_flag):
    control_flag = 1
    latency_config_group = 100
    get_difficulty_method = 'm1'

    items = ab_test_flag.strip().split('_')
    if len(items) > 2:
        try:
            control_flag = 1 if items[0] == 'con' else 0
            latency_config_group = int(items[1])
            get_difficulty_method = str(items[2])
        except:
            pass

    return control_flag, latency_config_group, get_difficulty_method
