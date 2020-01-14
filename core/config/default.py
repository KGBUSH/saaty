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

SQLALCHEMY_DATABASE_URI = 'mysql://dev_w:6nvjq0_HW@10.9.113.30:3306/saaty_db'

SQLALCHEMY_BINDS = {
    'saaty_db': 'mysql://dev_w:6nvjq0_HW@10.9.113.30:3306/saaty_db',
    'saaty_db_slave': 'mysql://dev_readonly:6nvjq0_H@10.9.113.30:3306/saaty_db',
    'dw_api_db': 'mysql://dev_readonly:6nvjq0_H@10.9.113.30:3306/dw_api',
    'dw_api_db_slave': 'mysql://dev_readonly:6nvjq0_H@10.9.113.30:3306/dw_api',
}

DEFAULT_DATABASE = 'saaty_db'

DADA_DATA_CLIENT_STRATEGY = [
    {
        'readOnly': False,
        'auth': {
            'username': 'dev_w',
            'password': '6nvjq0_HW',
            'schema': 'saaty_db',
        },
        'clientName': 'saaty_db',
        'cloudName': 'mysqldb019',
    },
    {
        'readOnly': True,
        'auth': {
            'username': 'dev_r',
            'password': 'Desx26read66',
            'schema': 'saaty_db',
        },
        'clientName': 'saaty_db_slave',
        'cloudName': 'mysqldb019',
        'ha': ['mysqlg019_r1'],
    },
    {
        'readOnly': False,
        'auth': {
            'username': 'dev_r',
            'password': 'Desx26read66',
            'schema': 'dw_api',
        },
        'clientName': 'dw_api_db',
        'cloudName': 'mysqldb022',
        'ha': ['mysqlg022_w1'],
    },
    {
        'readOnly': False,
        'auth': {
            'username': 'dev_r',
            'password': 'Desx26read66',
            'schema': 'dw_api',
        },
        'clientName': 'dw_api_db_slave',
        'cloudName': 'mysqldb022',
        'ha': ['mysqlg022_w1'],
    },
    {
        'clientName': 'default_redis',
        'cloudName': 'redisalone045',
        'clientType': 'standalone',
    },
]

LOCAL_MQ_CFG = {
    'RABBIT_MQ_TASK_INTERVAL': 1000,
    'saaty_routing_consumer_brokers': {
        'dc1': {
            'base': {
                'rabbit-saaty': {
                    'cluster_list': ['cluster1'],
                    'vhost': '%2Fsaaty',
                    'auth': 'admin:Pass1234'
                },
                'default': {
                    'cluster_list': ['cluster1'],
                    'vhost': '%2Fsaaty',
                    'auth': 'admin:Pass1234'
                }
            }
        }
    },
    'saaty_routing_producer_brokers': {
        'dc1': {
            'base': {
                'rabbit-saaty': {
                    'cluster_list': ['cluster1'],
                    'vhost': '%2Fsaaty',
                    'auth': 'admin:Pass1234'
                },
                'default': {
                    'cluster_list': ['cluster1'],
                    'vhost': '%2Fsaaty',
                    'auth': 'admin:Pass1234'
                }
            }
        }
    },
    'max.link.per.cluster': '1',
    'max.republished.count': '5',
    'message.queue.cluster.pool': {
        'cluster1': ['10.9.45.106:5672']
    },
    'msg.isolation.route.name': 'jd_cloud',
    'msg.queue.consumer.key.binds': {},
    'msg.queue.producer.key.binds': {},
    'only.record.err.log': 'true',
    'publish.need.ack': 'true'
}

SENTRY_DSN = ''

ZK_HOSTS = '10.9.82.249:2181'

LOCAL_CONSUL_HOST = 'consul.ndev.imdada.cn'
LOCAL_CONSUL_PORT = 80

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

POI_TIME_OVERHEAD_DEFAULT_VALUE_DEFAULT_CITY = {
  'pickup_time': 83,
  'pickup_rank': 0.5,
  'receiver_time': 116,
  'receiver_rank': 0.5
}

POI_TIME_OVERHEAD_DEFAULT_VALUE = {
  '1': {
    'pickup_time': 83,
    'pickup_rank': 0.5,
    'receiver_time': 116,
    'receiver_rank': 0.5
  },
  '2': {
    'pickup_time': 126,
    'pickup_rank': 0.5,
    'receiver_time': 151,
    'receiver_rank': 0.5
  },
  '3': {
    'pickup_time': 99,
    'pickup_rank': 0.5,
    'receiver_time': 143,
    'receiver_rank': 0.5
  },
  '4': {
    'pickup_time': 95,
    'pickup_rank': 0.5,
    'receiver_time': 133,
    'receiver_rank': 0.5
  },
  '5': {
    'pickup_time': 95,
    'pickup_rank': 0.5,
    'receiver_time': 123,
    'receiver_rank': 0.5
  },
  '6': {
    'pickup_time': 91,
    'pickup_rank': 0.5,
    'receiver_time': 157,
    'receiver_rank': 0.5
  },
  '7': {
    'pickup_time': 121,
    'pickup_rank': 0.5,
    'receiver_time': 136,
    'receiver_rank': 0.5
  },
  '8': {
    'pickup_time': 82,
    'pickup_rank': 0.5,
    'receiver_time': 124,
    'receiver_rank': 0.5
  },
  '9': {
    'pickup_time': 91,
    'pickup_rank': 0.5,
    'receiver_time': 134,
    'receiver_rank': 0.5
  },
  '10': {
    'pickup_time': 105,
    'pickup_rank': 0.5,
    'receiver_time': 164,
    'receiver_rank': 0.5
  },
  '11': {
    'pickup_time': 92,
    'pickup_rank': 0.5,
    'receiver_time': 150,
    'receiver_rank': 0.5
  },
  '12': {
    'pickup_time': 108,
    'pickup_rank': 0.5,
    'receiver_time': 188,
    'receiver_rank': 0.5
  },
  '13': {
    'pickup_time': 111,
    'pickup_rank': 0.5,
    'receiver_time': 172,
    'receiver_rank': 0.5
  },
  '14': {
    'pickup_time': 105,
    'pickup_rank': 0.5,
    'receiver_time': 183,
    'receiver_rank': 0.5
  },
  '15': {
    'pickup_time': 83,
    'pickup_rank': 0.5,
    'receiver_time': 124,
    'receiver_rank': 0.5
  },
  '16': {
    'pickup_time': 87,
    'pickup_rank': 0.5,
    'receiver_time': 141,
    'receiver_rank': 0.5
  },
  '17': {
    'pickup_time': 87,
    'pickup_rank': 0.5,
    'receiver_time': 142,
    'receiver_rank': 0.5
  },
  '18': {
    'pickup_time': 75,
    'pickup_rank': 0.5,
    'receiver_time': 133,
    'receiver_rank': 0.5
  },
  '19': {
    'pickup_time': 76,
    'pickup_rank': 0.5,
    'receiver_time': 124,
    'receiver_rank': 0.5
  },
  '21': {
    'pickup_time': 73,
    'pickup_rank': 0.5,
    'receiver_time': 110,
    'receiver_rank': 0.5
  },
  '22': {
    'pickup_time': 91,
    'pickup_rank': 0.5,
    'receiver_time': 130,
    'receiver_rank': 0.5
  },
  '23': {
    'pickup_time': 152,
    'pickup_rank': 0.5,
    'receiver_time': 173,
    'receiver_rank': 0.5
  },
  '24': {
    'pickup_time': 130,
    'pickup_rank': 0.5,
    'receiver_time': 195,
    'receiver_rank': 0.5
  },
  '25': {
    'pickup_time': 76,
    'pickup_rank': 0.5,
    'receiver_time': 126,
    'receiver_rank': 0.5
  },
  '26': {
    'pickup_time': 72,
    'pickup_rank': 0.5,
    'receiver_time': 137,
    'receiver_rank': 0.5
  },
  '27': {
    'pickup_time': 77,
    'pickup_rank': 0.5,
    'receiver_time': 128,
    'receiver_rank': 0.5
  },
  '28': {
    'pickup_time': 83,
    'pickup_rank': 0.5,
    'receiver_time': 122,
    'receiver_rank': 0.5
  },
  '29': {
    'pickup_time': 102,
    'pickup_rank': 0.5,
    'receiver_time': 153,
    'receiver_rank': 0.5
  },
  '30': {
    'pickup_time': 116,
    'pickup_rank': 0.5,
    'receiver_time': 145,
    'receiver_rank': 0.5
  },
  '31': {
    'pickup_time': 78,
    'pickup_rank': 0.5,
    'receiver_time': 138,
    'receiver_rank': 0.5
  },
  '32': {
    'pickup_time': 77,
    'pickup_rank': 0.5,
    'receiver_time': 127,
    'receiver_rank': 0.5
  },
  '35': {
    'pickup_time': 69,
    'pickup_rank': 0.5,
    'receiver_time': 121,
    'receiver_rank': 0.5
  },
  '36': {
    'pickup_time': 75,
    'pickup_rank': 0.5,
    'receiver_time': 123,
    'receiver_rank': 0.5
  },
  '37': {
    'pickup_time': 93,
    'pickup_rank': 0.5,
    'receiver_time': 128,
    'receiver_rank': 0.5
  },
  '38': {
    'pickup_time': 99,
    'pickup_rank': 0.5,
    'receiver_time': 155,
    'receiver_rank': 0.5
  },
  '39': {
    'pickup_time': 91,
    'pickup_rank': 0.5,
    'receiver_time': 152,
    'receiver_rank': 0.5
  },
  '40': {
    'pickup_time': 78,
    'pickup_rank': 0.5,
    'receiver_time': 125,
    'receiver_rank': 0.5
  },
  '66': {
    'pickup_time': 71,
    'pickup_rank': 0.5,
    'receiver_time': 72,
    'receiver_rank': 0.5
  },
  '76': {
    'pickup_time': 141,
    'pickup_rank': 0.5,
    'receiver_time': 223,
    'receiver_rank': 0.5
  },
  '77': {
    'pickup_time': 147,
    'pickup_rank': 0.5,
    'receiver_time': 199,
    'receiver_rank': 0.5
  },
  '116': {
    'pickup_time': 102,
    'pickup_rank': 0.5,
    'receiver_time': 128,
    'receiver_rank': 0.5
  },
  '135': {
    'pickup_time': 135,
    'pickup_rank': 0.5,
    'receiver_time': 175,
    'receiver_rank': 0.5
  },
  '180': {
    'pickup_time': 94,
    'pickup_rank': 0.5,
    'receiver_time': 127,
    'receiver_rank': 0.5
  },
  '357': {
    'pickup_time': 88,
    'pickup_rank': 0.5,
    'receiver_time': 110,
    'receiver_rank': 0.5
  },
  '358': {
    'pickup_time': 63,
    'pickup_rank': 0.5,
    'receiver_time': 107,
    'receiver_rank': 0.5
  }
}
