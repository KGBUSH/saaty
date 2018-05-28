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
