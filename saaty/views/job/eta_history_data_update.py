# -*- coding: utf-8 -*-

from common.framework.views import JsonView
from job.tasks.eta_history_data_update_task import \
    update_supplier_history_data, update_transporter_history_data

__all__ = [
    "ETASupplierHistoryUpdateJob",
    "ETATransporterHistoryUpdateJob",
]


class ETASupplierHistoryUpdateJob(JsonView):
    methods = ['POST', ]
    decorators = []

    def post(self, *args, **kwargs):
        contex = {}
        update_supplier_history_data.delay()
        return self.render_to_response(contex)


class ETATransporterHistoryUpdateJob(JsonView):
    methods = ['POST', ]
    decorators = []

    def post(self, *args, **kwargs):
        contex = {}
        update_transporter_history_data.delay()
        return self.render_to_response(contex)
