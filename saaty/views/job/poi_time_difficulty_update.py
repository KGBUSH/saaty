# -*- coding: utf-8 -*-

from common.framework.views import JsonView
from job.tasks.poi_time_difficulty_update_task import \
    update_poi_supplier_pickup_time_data

__all__ = [
    "POITimeSupplierDifficultyUpdateJob",
]


class POITimeSupplierDifficultyUpdateJob(JsonView):
    methods = ['POST', ]
    decorators = []

    def post(self, *args, **kwargs):
        contex = {}
        update_poi_supplier_pickup_time_data.delay()
        return self.render_to_response(contex)
