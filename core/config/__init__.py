# -*- coding: utf-8 -*-

import os

from .default import *

try:
    from .local import *
except ImportError:
    pass

APP_ENV = os.getenv('APP_ENV', 'LOCAL')

if APP_ENV != 'LOCAL':
    ZK_HOSTS = os.getenv('ZK_HOSTS')
    CFG_SERVICE = True
    CFG_REDIS = os.getenv('CFG_REDIS')
    CFG_USE_LOCAL = False
