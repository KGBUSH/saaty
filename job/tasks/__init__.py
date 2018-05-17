# -*- coding: utf-8 -*-

from job.tasks import poi_time_difficulty_update_task


tasks = [
    # job_update_poi_supplier_pickup_time_data
    poi_time_difficulty_update_task.update_poi_supplier_pickup_time_data,

]
