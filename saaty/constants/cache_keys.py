# -*- coding: utf-8 -*-

ALL_CITY_LIST = 'all_city_list'

# 发货地取货时间开销
CACHE_KEY_PICKUP_TIME_OVERHEAD = 'saaty_pickup_time_overhead_cache_key_' \
                                 '{cityId}_{supplierId}_{supplierLng}_' \
                                 '{supplierLat}'

# 收货地取货时间开销
CACHE_KEY_RECEIVER_TIME_OVERHEAD = 'saaty_receiver_time_overhead_cache_key_' \
                                   '{cityId}_{receiverLng}_{receiverLat}'

# 商户取货难度系数
SUPPLIER_TIME_DIFFICULTY = 'supplier_time_difficulty_{supplier_id}_' \
                           '{supplier_lng}_{supplier_lat}_{city_id}'

# POI 送达难度系数
RECEIVER_TIME_DIFFICULTY = 'receiver_time_difficulty_{receiver_lng}_' \
                           '{receiver_lat}_{city_id}'
