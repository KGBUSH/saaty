# -*- coding: utf-8 -*-

ALL_CITY_LIST = 'all_city_list'


# 发货地取货时间开销
CACHE_KEY_PICKUP_TIME_OVERHEAD = 'saaty_pickup_time_overhead_cache_key_' \
                                 '{cityId}_{supplierId}_{supplierLng}_' \
                                 '{supplierLat}'

# 收货地取货时间开销
CACHE_KEY_RECEIVER_TIME_OVERHEAD = 'saaty_receiver_time_overhead_cache_key_' \
                                   '{cityId}_{receiverLng}_{receiverLat}'
