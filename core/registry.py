# -*- coding: utf-8 -*-

from consul import Consul
from common.registry.registry_client import DefaultRegistryClient
from common.registry.discovery_client import DefaultDiscoveryClient


__all__ = [
    'create_consul',
    'RegistryService',
    'DiscoveryService',
]


METHOD_CATALOG = {}


def create_consul(app):
    if app.config['APP_ENV'] in ('LOCAL', ):
        consul = Consul(
            host=app.config['LOCAL_CONSUL_HOST'],
            port=app.config['LOCAL_CONSUL_PORT'],
        )
    else:
        consul = Consul()
    return consul


class RegistryService(object):
    """
    服务注册
    """

    def __init__(self, app):
        self.app = app
        self.service_id = None
        self.client = DefaultRegistryClient(
            consul=create_consul(app),
        )

    def register(self, register_name=None):
        if register_name is None:
            register_name = self.app.config['APP_NAME']

        app_name = register_name
        app_env = self.app.config['APP_ENV']
        health_check_url = self.app.config.get('HTTP_HEALTH_CHECK_URL')

        if self.client.is_registered(
            name=app_name,
            port=80,
        ):
            if self.service_id is None:
                self.client.close()
            else:
                return

        self.service_id = self.client.register(
            name=app_name,
            port=80,
            env=app_env,
            health_check_url=health_check_url,
        )

        return self.service_id

    def __del__(self):
        self.client.close()


class DiscoveryService(object):
    """
    服务发现
    """

    def __init__(self, app, service_id=None, method_catalog=None):
        self.app = app
        if method_catalog is None:
            method_catalog = {}
        self.method_catalog = method_catalog
        self.client = DefaultDiscoveryClient(
            consul_client=create_consul(app),
            service_id=service_id,
            method_catalog=self.method_catalog,
        )
        self.service_id = service_id

    def init(self):
        self.client.init()

    def __del__(self):
        self.client.close()

    def get_service_endpoint(self, service, method=None, return_host=False, scheme='http'):
        return self.client.get_service_endpoint(
            service=service, method=method,
            return_host=return_host, scheme=scheme,
        )

    def update_method_catalog(self, service, service_method):
        self.method_catalog.update({service: service_method})

    @property
    def service_id(self):
        return self.client.service_id

    @service_id.setter
    def service_id(self, service_id):
        self.client.service_id = service_id

    def handle_event(self, event):
        """
        compat method
        """

    def get_host_health(self):
        """
        compat method
        """
