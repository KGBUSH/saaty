# -*- coding: utf-8 -*-

from common.framework.views import JsonView
<<<<<<< HEAD
<<<<<<< HEAD
from job.tasks.poi_time_difficulty_update_task import \
=======
from saaty.job.tasks.poi_time_difficulty_update_task import \
>>>>>>> [add] add jobs
=======
from job.tasks.poi_time_difficulty_update_task import \
>>>>>>> [update] update job worker
    update_poi_supplier_pickup_time_data

__all__ = [
    "POITimeSupplierDifficultyUpdateJob",
]


class POITimeSupplierDifficultyUpdateJob(JsonView):
    methods = ['POST', ]
    decorators = []

    def post(self, *args, **kwargs):
        contex = {}
<<<<<<< HEAD
<<<<<<< HEAD
        update_poi_supplier_pickup_time_data.delay()
=======
        update_poi_supplier_pickup_time_data()
>>>>>>> [add] add jobs
=======
        update_poi_supplier_pickup_time_data.delay()
>>>>>>> [update] update job worker
        return self.render_to_response(contex)
