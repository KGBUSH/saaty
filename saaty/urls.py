# -*- coding: utf-8 -*-

from saaty.views.admin import CheckHealthView


urls = [
    # ADMIN
    ('/admin/healthcheck', CheckHealthView.as_view('health_check')),
]
