# -*- coding: utf-8 -*-

import os
import time
import json
import threading
import requests
import traceback

from common.registry.discovery_client import BadConnection
from common.utils.net_utils import local_ip

from core import http_pool

from core import app
from core import log
from core import kafkaBizLogger
from core import freeKafkaLogger


__author__ = 'circle'


SERVICE_HEADER_KEY = 'dada-service'

local = threading.local()
RPC_STATS_REPORT_INTERVAL = 60

default_service_timeout = 4
default_service_retry = 1


def add_stats(system, host):

    if '__APP_NAME__' not in app.config:
        return
    if not hasattr(local, 'rpc_stats'):
        local.rpc_stats = {}
    if not hasattr(local, 'rpc_stats_report_time'):
        now = int(time.time())
        local.rpc_stats_report_time = now - now % RPC_STATS_REPORT_INTERVAL

    rpc_stats = local.rpc_stats
    if system in rpc_stats:
        system_stats = rpc_stats[system]
        if host in system_stats:
            system_stats[host] += 1
        else:
            system_stats[host] = 1
    else:
        rpc_stats[system] = {
            host: 1
        }
    report_stats()


def report_stats():

    def obj_to_json(obj):
        return json.dumps(obj, ensure_ascii=False, encoding='utf-8', default=lambda obj: obj.__dict__)

    last_report_time = local.rpc_stats_report_time
    now = int(time.time())
    if now - last_report_time < RPC_STATS_REPORT_INTERVAL:
        return
    rpc_stats = local.rpc_stats
    if len(rpc_stats) > 0:
        t = threading.current_thread()
        data = {
            'thread': t.name,
            'stats': rpc_stats
        }
        msg = 'stats\t{0}\t{1}\t{2}\t{3}'.format(last_report_time, app.config['__APP_NAME__'], local_ip,
                                                 obj_to_json(data))
        freeKafkaLogger.info_with_topic('topic_rpc_error', msg)
    local.rpc_stats = {}
    local.rpc_stats_report_time = now - now % RPC_STATS_REPORT_INTERVAL


def get(category, service_name, service_params=None, timeout=default_service_timeout, retry=default_service_retry,
        query_params=None, **kwargs):
    from core import discovery_service
    default_headers = {
        SERVICE_HEADER_KEY: service_name
    }

    headers = kwargs.get('headers', default_headers)
    retries = 0
    host = None
    url = None
    while True:
        try:
            url, host = get_url_with_host(category, service_name, service_params)
            add_stats(category, host)
            response = http_pool.get(url, headers=headers, params=query_params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except:
            traceback.print_exc()
            retries += 1
            if host is not None:
                discovery_service.handle_event(BadConnection(host))
            if retries > retry:
                host_health = discovery_service.get_host_health()
                log.info('request to %s failed, retries exceeded. (%s)' % (host, str(host_health)))
                log_rpc_error(category, service_name, service_params, '', host, url)
                raise
            else:
                log.info('request to %s failed, retrying...' % host)


def get_with_url(url, params=None, timeout=None, retry=False, error_result=None):
    http_client = get_http_pool(retry)
    add_stats('default', '')
    try:
        response = http_client.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except:
        log_rpc_error('default', 'default', '', params, '', url)
        return error_result


def get_with_tuple(category, service_name, retry=False, service_params=None, timeout=1):
    url, host = get_url_with_host(category, service_name, service_params)
    add_stats(category, host)

    result = None
    begin_time = time.time()
    try:
        response = get_http_pool(retry).get(url, timeout=timeout)
        response.raise_for_status()
        if response is not None:
            result = ('ok', response.status_code, response.json())
        else:
            result = ('fail', '000', 'request failed')

    except requests.ConnectionError as e:
        result = ('fail', '000', 'request failed')
        log_rpc_error(category, service_name, service_params, '', host, url)
    except Exception as  e:
        result = ('fail', '000', 'request failed')
        log_rpc_error(category, service_name, service_params, '', host, url)
    finally:
        return result


def get_http_pool(retry=False):
    # if retry:
    #     return http_pool_with_retry
    # else:
    return http_pool


def post(category, service_name, service_params=None, data=None, timeout=default_service_timeout, **kwargs):
    url, host = get_url_with_host(category, service_name, service_params)
    add_stats(category, host)
    default_headers = {
        'content-type': 'application/json',
        SERVICE_HEADER_KEY: service_name
    }

    headers = kwargs.get('headers', default_headers)
    try:
        response = http_pool.post(url, data=data, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except:
        log_rpc_error(category, service_name, service_params, '', host, url)
        raise


def delete(category, service_name, service_params=None, data=None, timeout=default_service_timeout):
    url, host = get_url_with_host(category, service_name, service_params)
    add_stats(category, host)
    headers = {
        'content-type': 'application/json',
        SERVICE_HEADER_KEY: service_name
    }
    try:
        response = http_pool.delete(url, data=data, headers=headers, timeout=timeout)
        response.raise_for_status()
    except:
        log_rpc_error(category, service_name, service_params, '', host, url)
        raise


def get_url(category, service_name, service_params=None):
    from core import discovery_service
    discovery_service.init()
    service_endpoint = discovery_service.get_service_endpoint(category, service_name)
    url = service_endpoint
    if service_params is not None:
        url = service_endpoint.format(*service_params)

    return url


def get_url_with_host(category, service_name, service_params=None):
    from core import discovery_service
    discovery_service.init()
    service_endpoint, host = discovery_service.get_service_endpoint(category, service_name, return_host=True)
    url = service_endpoint
    if service_params is not None:
        url = service_endpoint.format(*service_params)

    return url, host


def post_once(category, service_name, service_params=None, data=None, timeout=default_service_timeout):
    url, host = get_url_with_host(category, service_name, service_params)
    add_stats(category, host)
    headers = {
        'content-type': 'application/json',
        SERVICE_HEADER_KEY: service_name
    }
    try:
        response = http_pool.post(url, data=data, headers=headers, timeout=timeout)
        response.raise_for_status()
    except:
        log_rpc_error(category, service_name, service_params, '', host, url)
        raise


def get_url_once(category, service_name, service_params=None):
    from core import discovery_service
    discovery_service.init_only_once()
    service_endpoint = discovery_service.get_service_endpoint(category, service_name)
    url = service_endpoint
    if service_params is not None:
        url = service_endpoint.format(*service_params)
    log.info("[pid: %s, modelservice.url: %s]" % (os.getpid(), url))
    return url


def log_rpc_error(category, service_name, service_params, data, host, url):

    def current_exception_info():
        import sys
        import traceback
        try:
            exc_type, exc_value, exc_tb = sys.exc_info()
            exc_list = traceback.format_exception(exc_type, exc_value, exc_tb)
            if len(exc_list) > 0:
                exc_list.insert(0, exc_list[len(exc_list) - 1])
                exc_list.pop(len(exc_list) - 1)
            return "".join(exc_list)
        except:
            pass
        return " error... "

    def obj_to_json(obj):
        return json.dumps(obj, ensure_ascii=False, encoding='utf-8', default=lambda obj: obj.__dict__)

    rpc_error_msg = {
        'app_name': category,
        'service_name': service_name,
        'service_params': service_params,
        'data': data,
        'host': host,
        'url': url.replace('/', '_'),
        'exception': current_exception_info(),
    }

    kafkaBizLogger.info(10038, rpc_error_msg)

    if '__APP_NAME__' in app.config:
        data = {
            'source': app.config['__APP_NAME__'],
            'target': category,
            'host': host,
            'url': url,
            'service': service_name,
            'service_param': service_params,
            'service_data': data,
            'exception': current_exception_info()
        }
        now = int(time.time())
        msg = 'error\t{0}\t{1}\t{2}\t{3}'.format(now, app.config['__APP_NAME__'], local_ip,
                                                 obj_to_json(data))
        rpc_error_msg['system'] = app.config['__APP_NAME__']
        freeKafkaLogger.info_with_topic('topic_rpc_error', msg)
