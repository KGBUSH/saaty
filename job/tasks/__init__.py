# -*- coding: utf-8 -*-

from job.tasks import poi_time_difficulty_update_task
from job.tasks import poi_time_cost_update_task
from job.tasks import artificial_address_update_task
from job.tasks import eta_history_data_update_task


tasks = [
    # job_update_poi_supplier_pickup_time_data
    poi_time_difficulty_update_task.update_poi_supplier_pickup_time_data,

    # job_update_poi_receiver_time_data
    poi_time_difficulty_update_task.update_poi_receiver_time_data,

    # job_update_receiver_time_cost_data
    poi_time_cost_update_task.update_receiver_time_cost_data,

    # job_update_poi_pickup_time_cost_data
    poi_time_cost_update_task.update_poi_pickup_time_cost_data,

    # job_update_artificial_address_data 
    artificial_address_update_task.update_artificial_address_data,

    # job_update_supplier_history_data
    eta_history_data_update_task.update_supplier_history_data,

    # job_update_transporter_history_data
    eta_history_data_update_task.update_transporter_history_data,

    # job_update_poi_statistics_data
    eta_history_data_update_task.update_poi_statistics_data,

    # job_update_transporter_peak_data
    eta_history_data_update_task.update_transporter_peak_data

]