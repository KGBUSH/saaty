# -*- coding: utf-8 -*-

from saaty.views.admin import CheckHealthView
from saaty.views.v1.poi_latency_ratio import POILatencyRatioView
from saaty.views.v1.pickup_time_overhead import PickupTimeOverHeadView
from saaty.views.v1.receiver_time_overhead import ReceiverTimeOverHeadView
from saaty.views.job.poi_time_difficulty_update import \
    POITimeSupplierDifficultyUpdateJob, POITimeReceiverDifficultyUpdateJob
from saaty.views.job.poi_time_cost_update import \
    POITimeReceiverTimeCostUpdateJob, POITimeSupplierPickupTimeCostUpdateJob

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

# JOBS
urls.extend([
    # update POI supplier pickup time difficulty info
    ('/job/update_poi_time_supplier_data', POITimeSupplierDifficultyUpdateJob
     .as_view('job_update_poi_time_supplier_data')),

    # update POI receiver time difficulty info
    ('/job/update_poi_time_receiver_data', POITimeReceiverDifficultyUpdateJob
     .as_view('job_update_poi_time_receiver_data')),

    # update POI receiver time cost info
    ('/job/update_receiver_time_cost_data', POITimeReceiverTimeCostUpdateJob
     .as_view('job_update_receiver_time_cost_data')),

    # update POI supplier pickup time cost info
    ('/job/update_supplier_time_cost_data',
     POITimeSupplierPickupTimeCostUpdateJob.as_view(
         'job_update_poi_pickup_time_cost_data')),

])
