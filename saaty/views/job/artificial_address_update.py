# -*- coding: utf-8 -*-

"""

@author: zhenfengjiang

@contact: zhenfengjiang@imdada.cn

@file: artificial_address_update.py

@time: 2019/9/6 14:23

@desc:

"""

from common.framework.views import JsonView
from job.tasks.artificial_address_update_task import \
    update_artificial_address_data


class ArtificialAddressInfoUpdateJob(JsonView):
    methods = ['POST', ]
    decorators = []

    def post(self, *args, **kwargs):
        contex = {}
        update_artificial_address_data.delay()
        return self.render_to_response(contex)
