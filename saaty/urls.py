# -*- coding: utf-8 -*-

from saaty.views.admin import CheckHealthView
from saaty.views.v1.poi_latency_ratio import POILatencyRatioView
from saaty.views.v1.dynamic_pickup_arrive_latency import DynamicPickupArriveLatencyView
from saaty.views.v1.pickup_time_overhead import PickupTimeOverHeadView
from saaty.views.v1.receiver_time_overhead import ReceiverTimeOverHeadView
from saaty.views.v1.eta_A_overhead import EtaAOverHeadView, EtaABatchOverHeadView
from saaty.views.v1.eta_C_overhead import EtaCOverHeadView
from saaty.views.job.poi_time_difficulty_update import \
    POITimeSupplierDifficultyUpdateJob, POITimeReceiverDifficultyUpdateJob
from saaty.views.job.poi_time_cost_update import \
    POITimeReceiverTimeCostUpdateJob, POITimeSupplierPickupTimeCostUpdateJob
from saaty.views.job.artificial_address_update import ArtificialAddressInfoUpdateJob
from saaty.views.job.eta_history_data_update import ETASupplierHistoryUpdateJob,ETATransporterHistoryUpdateJob, \
    ETAPoiStatisticsUpdateJob,ETATransporterPeakUpdateJob

urls = [
    # ADMIN
    ('/admin/healthcheck', CheckHealthView.as_view('health_check')),

    # POI time rank
    ('/v1/poi_time_latency', POILatencyRatioView.as_view('poi_latency')),

    # VIP_ASSIGN dynamic pickup_latency and arrive_latency
    ('/v1/dynamic_pickup_arrive_latency', DynamicPickupArriveLatencyView.as_view('dynamic_latency')),

    # supplier time overhead
    ('/v1/pickup_time_overhead', PickupTimeOverHeadView.as_view('pickup_time')),

    # receiver time overhead
    ('/v1/receiver_time_overhead', ReceiverTimeOverHeadView.as_view(
        'receiver_time')),

    # eta: accept_to_pickup time (total A) overhead
    ('/v1/eta/accept_to_pickup', EtaAOverHeadView.as_view('eta_a_time_overhead')),

    # eta: accept_to_pickup time (total A) overhead
    ('/v1/eta/accept_to_pickup_batch', EtaABatchOverHeadView.as_view('eta_a_time_batch_overhead')),

    # eta: delivery time (C) overhead
    ('/v1/eta/delivery', EtaCOverHeadView.as_view('eta_c_time_overhead')),

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

    # 更新人工困难地址
    ('/job/update_artificial_address_data',
     ArtificialAddressInfoUpdateJob.as_view(
         'job_update_artificial_address_data')),

    # ETA: update supplier history info
    ('/job/update_supplier_history_data', ETASupplierHistoryUpdateJob
     .as_view('job_update_eta_supplier_history_data')),

    # ETA: update transporter history info
    ('/job/update_transporter_history_data', ETATransporterHistoryUpdateJob
     .as_view('job_update_eta_transporter_history_data')),

    # ETA: poi statistics info
    ('/job/update_poi_statistics_data', ETAPoiStatisticsUpdateJob
     .as_view('job_update_eta_poi_statistics_data')),

    # ETA: transporter peak info
    ('/job/update_transporter_peak_data', ETATransporterPeakUpdateJob
     .as_view('job_update_eta_transporter_peak_data')),
])
