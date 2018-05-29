#!/usr/bin/python
# -*- coding: utf-8 -*-

import cPickle as pickle


def save_object(obj, file_path):
    f = file(file_path, 'wb')
    pickle.dump(obj, f, True)
    f.close()
    print("%s saved successfully!" % file_path)


def load_object(file_path):
    f = file(file_path, 'rb')
    obj = pickle.load(f)
    print("%s loaded successfully!" % file_path)
    f.close()
    return obj


def normalize(weight_value, weight_min, weight_max):
    # 根据 该特征字段 的 最大最小值 计算当前取值 的 归一化值
    v_normalized = (weight_value - weight_min) / (weight_max - weight_min)
    if v_normalized > 1:
        return 1.0
    elif v_normalized < 0:
        return 0.0
    else:
        return v_normalized
