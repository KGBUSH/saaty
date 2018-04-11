# -*- coding: utf-8 -*-

from saaty.views.admin import CheckHealthView
from saaty.views.v1.poi_latency_ratio import POILatencyRatioView


urls = [
    # ADMIN
    ('/admin/healthcheck', CheckHealthView.as_view('health_check')),
    # POI time rank
    ('/v1/poi_time_latency', POILatencyRatioView.as_view('poi_latency'))
]
