#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 xuekun.zhuang <zhuangxuekun@imdada.cn>


# -*- coding: utf-8 -*-

from common.framework.views import JsonView


__all__ = [
    'CheckHealthView',
]


class CheckHealthView(JsonView):
    """
    健康检查
    """

    methods = ['GET', ]

    decorators = []

    def get_context_data(self, **kwargs):
        return {}