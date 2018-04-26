# -*- coding: utf-8 -*-

import sys
import logging
import importlib
from flask import Flask
from requests import Session
from redis import Redis
from requests_futures.sessions import FuturesSession
from werkzeug.contrib.profiler import ProfilerMiddleware
from kazoo.client import KazooClient
from raven.contrib.flask import Sentry
from common.db.router import AutoRouteSQLAlchemy
from common.mq.kafka_logger import BizkafkaLogger
from common.mq.kafka_logger import FreeKafkaLogger
from common.config.cfgservice import Cfgservice
from common.cache.dadacache import DadaCache
from core.registry import RegistryService
from core.registry import DiscoveryService
from core import config

app = Flask('saaty')
app.config.from_object(config)
app.config['__APP_NAME__'] = config.APP_NAME

# zookeeper client
zk_client = KazooClient(
    hosts=app.config['ZK_HOSTS'],
    connection_retry={
        'max_tries': -1,
        'delay': 2,
        'backoff': 2,
    },
    timeout=30.0,
)
zk_client.start()

# config service
config_service = Cfgservice(
    app=app,
    system_name=app.config['APP_NAME'],
    zk_client=zk_client,
    use_local=app.config['CFG_USE_LOCAL'],
)
if app.config['CFG_SERVICE']:
    config_service.init()

# database
db = AutoRouteSQLAlchemy(app)

# redis
redis = Redis(
    host=app.config['REDIS_HOST'],
    port=app.config['REDIS_PORT'],
    db=app.config['REDIS_DATABASE_INDEX'],
    socket_timeout=app.config.get('REDIS_SOCKET_TIMEOUT', 1),
    retry_on_timeout=True,
)

# cache
cache = DadaCache(app, config={
    'REDIS_OBJ': redis,
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': '127.0.0.1',
    'CACHE_REDIS_PORT': '6379',
    'CACHE_REDIS_DB': 0,
    'CACHE_DEFAULT_TIMEOUT': app.config['REDIS_SOCKET_TIMEOUT'],
    'CACHE_KEY_PREFIX': app.config['CACHE_KEY_PREFIX'],
})

# http client
http_pool = Session()
async_http_pool = FuturesSession(
    session=http_pool,
    max_workers=4,
)

# sentry client
sentry = Sentry(app)

# kafka logger
kafkaBizLogger = BizkafkaLogger(
    hosts_list=app.config['KAFKA_HOSTS_LIST'],
    topic_name=app.config['TOPIC_DADA_BIZ_LOG'],
    app_config=app.config,
)
freeKafkaLogger = FreeKafkaLogger(
    hosts_list=app.config['KAFKA_HOSTS_LIST'],
    app_config=app.config,
)

# registry service
registry_service = RegistryService(app)

# discovery service
discovery_service = DiscoveryService(app)

if app.config['PROFILE']:
    app.wsgi_app = ProfilerMiddleware(
        app=app.wsgi_app,
        restrictions=[30],
    )


def setup(register_name=None):
    # register & discovery
    service_id = registry_service.register(
        register_name=register_name,
    )
    discovery_service.service_id = service_id

    # urlconf
    root_urlconf = app.config.get('ROOT_URLCONF')
    if not root_urlconf:
        return
    url_module = importlib.import_module(root_urlconf)
    urls = getattr(url_module, 'urls', [])
    for url in urls:
        app.add_url_rule(url[0], view_func=url[-1])
    return app


# 日志服务
log = logging.getLogger('dada')
log.setLevel(logging.INFO)

# create console handler with a higher log level
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s-%(name)s-%(levelname)s-%(process)d-"
                              "%(processName)s-%(funcName)s %(message)s")
ch.setFormatter(formatter)
# add the handlers to logger
log.addHandler(ch)
