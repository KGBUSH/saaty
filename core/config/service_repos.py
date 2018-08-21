# -*- coding: utf-8 -*-

# delivery-center
SERVICE_RPC_DELIVERY_CENTER = 'delivery-center'

# 配送服务
ORDER_DETAIL_SINGLE = 'order.detail.single'
ORDER_DETAIL_BATCH = 'order.detail.batch'

# 服务注册仓库配置
SERVICE_REGISTRY_REPO = {
    SERVICE_RPC_DELIVERY_CENTER: {
        ORDER_DETAIL_SINGLE: '/order/detail/id',
        ORDER_DETAIL_BATCH: '/order/detail/ids'
    }
}
