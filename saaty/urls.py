# -*- coding: utf-8 -*-

from saaty.views.admin import CheckHealthView
from saaty.views.v1.poi_latency_ratio import POILatencyRatioView
from saaty.views.v1.pickup_time_overhead import PickupTimeOverHeadView
from saaty.views.v1.receiver_time_overhead import ReceiverTimeOverHeadView

urls = [
    # ADMIN
    ('/admin/healthcheck', CheckHealthView.as_view('health_check')),

    # POI time rank
    ('/v1/poi_time_latency', POILatencyRatioView.as_view('poi_latency')),

    # supplier time overhead
    ('/v1/pickup_time_overhead', PickupTimeOverHeadView.as_view('pickup_time')),

    # receiver time overhead
    ('/v1/receiver_time_overhead', ReceiverTimeOverHeadView.as_view(
        'receiver_time'))
]
