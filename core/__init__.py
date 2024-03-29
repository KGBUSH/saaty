# -*- coding: utf-8 -*-

import sys
import logging
import importlib
from flask import Flask
from werkzeug.contrib.profiler import ProfilerMiddleware
from kazoo.client import KazooClient
from raven.contrib.flask import Sentry
from common.db.router import AutoRouteSQLAlchemy
from common.mq.kafka_logger import BizkafkaLogger
from common.mq.kafka_logger import FreeKafkaLogger
from common.mq.rabbitmq_config import PropertiesBuilder
from common.mq.rabbit_integrate import integrate_producer
from common.mq.rabbit_integrate import integrate_consumer
from common.config.cfgservice import Cfgservice
from common.cache.dadacache import DadaCache
from common.dadadata import data_def
from common.dadadata import data_context
from common.metric import metric_util
from core.registry import RegistryService
from core.registry import DiscoveryService
from core.registry import ServiceFacade
from core import config
from core.config.service_repos import SERVICE_REGISTRY_REPO


def get_app_name():
    return app.config.get('__APP_NAME__', '0')


app = Flask('saaty')
app.config.from_object(config)
app.config['__APP_NAME__'] = config.APP_NAME
register_name = config.APP_REGISTER_NAME or config.APP_NAME


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


# registry service
registry_service = RegistryService(app)
service_id = registry_service.register(
    register_name=register_name,
)


# discovery service
discovery_service = DiscoveryService(app, service_id=service_id)
for _service, _service_method in SERVICE_REGISTRY_REPO.items():
    discovery_service.update_method_catalog(
        service=_service,
        service_method=_service_method,
    )


# dada data client
data_def.data_client_init(
    app=app,
    discovery_service=discovery_service,
)


# database
db = AutoRouteSQLAlchemy(app)


# mq client
mq_daemon_thread, mq_consumer = integrate_consumer(
    app=app,
    discovery_service=discovery_service.client,
    config_service=config_service,
    properties_builder=PropertiesBuilder(
        consumer_vhosts_key='saaty_routing_consumer_brokers',
    ),
)

mq_route_change_thread, mq_producer = integrate_producer(
    app=app,
    discovery_service=discovery_service.client,
    config_service=config_service,
    properties_builder=PropertiesBuilder(
        producer_vhosts_key='saaty_routing_producer_brokers',
    ),
)
mq_route_change_thread.start()


# redis & cache
redis = data_context.DataContext.redis_data_clients['default_redis']
cache = DadaCache(app, config={
    'REDIS_OBJ': redis,
    'CACHE_TYPE': 'redis',
    'CACHE_DEFAULT_TIMEOUT': app.config['REDIS_SOCKET_TIMEOUT'],
    'CACHE_KEY_PREFIX': app.config['CACHE_KEY_PREFIX'],
}, with_jinja2_ext=False)


# sentry client
sentry = Sentry(app)


# kafka logger
kafkaBizLogger = BizkafkaLogger(
    hosts_list=app.config['KAFKA_HOSTS_LIST'],
    topic_name=app.config['TOPIC_DADA_BIZ_LOG'],
    log_topic=app.config['TOPIC_DADA_BIZ_LOG'],
    app_config=app.config,
    discovery_service=discovery_service,
)
algoKafkaLogger = BizkafkaLogger(
    hosts_list=app.config['KAFKA_HOSTS_LIST'],
    topic_name=app.config['TOPIC_SAATY_BIZ_LOG'],
    log_topic=app.config['TOPIC_SAATY_BIZ_LOG'],
    app_config=app.config,
    discovery_service=discovery_service,
)
freeKafkaLogger = FreeKafkaLogger(
    hosts_list=app.config['KAFKA_HOSTS_LIST'],
    app_config=app.config,
    discovery_service=discovery_service,
)


# service facade
service_facade = ServiceFacade(
    discovery_client=discovery_service,
    system_name=config.APP_NAME,
    kafka_logger=freeKafkaLogger,
    max_workers=10,
)


if app.config['PROFILE']:
    app.wsgi_app = ProfilerMiddleware(
        app=app.wsgi_app,
        restrictions=[30],
    )


def setup():
    # urlconf
    root_urlconf = app.config.get('ROOT_URLCONF')
    if not root_urlconf:
        return
    url_module = importlib.import_module(root_urlconf)
    urls = getattr(url_module, 'urls', [])
    for url in urls:
        app.add_url_rule(url[0], view_func=url[-1])

    # metrics
    metric_util.init(
        app=app,
        discovery_service=service_facade,
    )
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
