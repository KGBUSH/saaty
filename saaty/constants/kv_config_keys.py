# -*- coding: utf-8 -*-

AREA_DYNAMIC_TIPS_FLAG = 'area_dynamic_tips_flag_{area_id}'     # 区域当前动态小费调节flag
GEOHASH_AREA_DYNAMIC_TIPS_FLAG = 'geohash_area_dynamic_tips_flag_{geohash_code}_{ab_test_id}'   # geohash区域当前动态小费调节flag
GEOHASH_AREA_MODEL_DYNAMIC_TIPS_FLAG = 'geohash_area_model_dynamic_tips_flag_{geohash_code}'  # geohash区域根据模型判断出的当前动态小费调节flag

CITY_SUPPLY_DEMAND_FLAG = 'city_supply_demand_flag_{city_id}'   # 城市供需状态标志
AREA_SUPPLY_DEMAND_FLAG = 'area_supply_demand_flag_{area_id}'   # 区域供需状态标志

PREVIOUS_AREA_SAMPLE_LIST = 'previous_area_sample_list_{area_id}_{premium_flag_method}'             # 区域之前的平均接单时长sample list
PREVIOUS_GEOHASH_SAMPLE_LIST = 'previous_geohash_sample_list_{geohash_code}_{premium_flag_method}'  # geohash区域之前的平均接单时长sample list

WEATHER_WARN_OPEN_STATUS = 'weather_warn_open_status_{city_id}'  # 天气预警-通知开关状态
WEATHER_WARN_PREMIUM_OPEN_STATUS = 'weather_warn_premium_open_status_{city_id}'  # 天气预警-溢价开关状态
WEATHER_WARN_VOICE_WARN_OPEN_STATUS = 'weather_warn_voice_warn_open_status_{city_id}'  # 当天是否电话通知到城市经理
