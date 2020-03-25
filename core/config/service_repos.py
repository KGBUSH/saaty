# -*- coding: utf-8 -*-

# 服务注册发现
SERVICE_RPC_DELIVERY_CENTER = 'delivery-center'  # delivery-center
SERVICE_RPC_HUBBLE_POI = 'hubble'  # hubble-poi

# service
ORDER_DETAIL_SINGLE = 'order.detail.single'
ORDER_DETAIL_BATCH = 'order.detail.batch'
LNG_LAT_POI_ID = 'latlng.poi.id'
ADDRESS_POI_ID = 'address.poi.id'
ADDRESS_POI_ID_NO_DIFFICULTY = 'address.poi.id.no.difficulty'


# 服务注册仓库配置
SERVICE_REGISTRY_REPO = {
    SERVICE_RPC_DELIVERY_CENTER: {
        ORDER_DETAIL_SINGLE: '/order/detail/id',
        ORDER_DETAIL_BATCH: '/order/detail/ids'
    },
    SERVICE_RPC_HUBBLE_POI : {
        LNG_LAT_POI_ID: '/v1/poi/get-info-by-latlng',
        ADDRESS_POI_ID: '/v1/poi/get-info-by-poiname',
        ADDRESS_POI_ID_NO_DIFFICULTY: '/v1/poi/get-normal-by-latlng'
    }
}
