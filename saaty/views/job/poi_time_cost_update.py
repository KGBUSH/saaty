# -*- coding: utf-8 -*-

from common.framework.views import JsonView
from job.tasks.poi_time_cost_update_task import \
    update_poi_pickup_time_cost_data, update_receiver_time_cost_data

__all__ = [
    "POITimeSupplierPickupTimeCostUpdateJob",
    "POITimeReceiverTimeCostUpdateJob",
]


class POITimeSupplierPickupTimeCostUpdateJob(JsonView):
    methods = ['POST', ]
    decorators = []

    def post(self, *args, **kwargs):
        contex = {}
        update_poi_pickup_time_cost_data.delay()
        return self.render_to_response(contex)


class POITimeReceiverTimeCostUpdateJob(JsonView):
    methods = ['POST', ]
    decorators = []

    def post(self, *args, **kwargs):
        contex = {}
        update_receiver_time_cost_data.delay()
        return self.render_to_response(contex)
