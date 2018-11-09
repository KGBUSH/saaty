# -*- coding: utf-8 -*-

import os

PROJECT_PATH = os.path.abspath(
    os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        os.pardir,
        os.pardir))

APP_NAME = __APP_NAME__ = 'saaty'

DEBUG = False

# 单次查询取货时间，sql最大条目
PICKUP_TIME_SQL_MAX_ONCE = 50

# 单次查询送达时间，sql最大条目
RECEIVER_TIME_SQL_MAX_ONCE = 50

ROOT_URLCONF = 'saaty.urls'

WTF_CSRF_ENABLED = False

HTTP_HEALTH_CHECK_URL = '/admin/healthcheck'

CFG_SERVICE = False
CFG_USE_LOCAL = False
CFG_REDIS = '10.9.36.145:6379'

PROFILE = False

SQLALCHEMY_TRACK_MODIFICATIONS = True

SQLALCHEMY_BINDS = {
    'saaty': 'mysql://dev_w:6nvjq0_HW@10.9.113.30:3306/saaty_db',
    'saaty_slave': 'mysql://dev_readonly:6nvjq0_H@10.9.113.30:3306/saaty_db',
    'dw_api_db': 'mysql://dev_readonly:6nvjq0_H@10.9.113.30:3306/dw_api',
    'dw_api_db_slave': 'mysql://dev_readonly:6nvjq0_H@10.9.113.30:3306/dw_api',
}

SENTRY_DSN = ''

ZK_HOSTS = '10.9.82.249:2181'

KAFKA_HOSTS_LIST = '10.9.101.106:9092'
TOPIC_SAATY_BIZ_LOG = 'topic_saaty'
TOPIC_DADA_BIZ_LOG = 'topic_dada_biz_log'
KAFKA_CLIENT_TYPE = 'kpy'
KAFKA_LOGGING_SWITCH = False

# Redis & Cache
REDIS_HOST = '10.9.166.48'
REDIS_PORT = 6379
REDIS_SOCKET_TIMEOUT = 0.1
REDIS_DATABASE_INDEX = 0

CACHE_KEY_PREFIX = 'saaty:'

# mq client config
SAATY_ROUTING_CONSUMER_BROKERS = {
    'dev/rabbit/rabbit-saaty': 'amqp://saaty:Pass1234@10.9.45.106:5672/%2Fsaaty',
    'dev/rabbit/default': 'amqp://saaty:Pass1234@10.9.45.106:5672/%2Fsaaty'
}

SAATY_ROUTING_PRODUCER_BROKERS = {
    'dev/rabbit/rabbit-saaty': 'amqp://saaty:Pass1234@10.9.45.106:5672/%2Fsaaty',
    'dev/rabbit/default': 'amqp://saaty:Pass1234@10.9.45.106:5672/%2Fsaaty'
}

RABBIT_HBASE_THRIFT_HOST = ''
RABBIT_HBASE_THRIFT_PORT = 0
RABBIT_HBASE_TABLE = ''

RABBIT_REDIS_HOST = ''
RABBIT_REDIS_PORT = 0

MQ_CURRENT_ENVIRONMENT = 'dev'
