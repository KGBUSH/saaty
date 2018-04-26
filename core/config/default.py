# -*- coding: utf-8 -*-

import os

PROJECT_PATH = os.path.abspath(
    os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        os.pardir,
        os.pardir))

APP_NAME = __APP_NAME__ = 'saaty'

DEBUG = False

#单次查询取货时间，sql最大条目
PICKUP_TIME_SQL_MAX_ONCE = 50

#单次查询送达时间，sql最大条目
RECEIVER_TIME_SQL_MAX_ONCE = 50


ROOT_URLCONF = 'saaty.urls'

WTF_CSRF_ENABLED = False

HTTP_HEALTH_CHECK_URL = '/admin/healthcheck'

CFG_SERVICE = False
CFG_USE_LOCAL = False

PROFILE = False

SQLALCHEMY_TRACK_MODIFICATIONS = True

SQLALCHEMY_BINDS = {
    'saaty': 'mysql://dev_w:6nvjq0_HW@192.168.1.250:3307/saaty_db',
    'saaty_slave': 'mysql://dev_readonly:6nvjq0_H@192.168.1.250:3307/saaty_db',
}

SENTRY_DSN = ''

ZK_HOSTS = '192.168.1.250:2181,192.168.1.250:2182,192.168.1.250:2183'

KAFKA_HOSTS_LIST = '192.168.1.250:9092'
TOPIC_DADA_BIZ_LOG = 'topic_dada_biz_log'
KAFKA_CLIENT_TYPE = 'kpy'
KAFKA_LOGGING_SWITCH = False

# Redis & Cache
REDIS_HOST = '192.168.1.250'
REDIS_PORT = 6379
REDIS_SOCKET_TIMEOUT = 0.1
REDIS_DATABASE_INDEX = 0

CACHE_KEY_PREFIX = 'saaty:'
