# -*- coding: utf-8 -*-


def get_vip_label(label_list):
    is_vip_assign = 0
    label_list = set(label_list.split(","))

    if "287" in label_list:
        is_vip_assign = 1

    return is_vip_assign


def get_order_category(label_list):
    label_list = set(label_list.split(","))
    if "160" in label_list and "140" in label_list:
        return "ac"
    if "160" in label_list:
        return "a"
    if "49" in label_list:
        return "dj"
    if "35" in label_list:
        return "bq"
    return "b"
