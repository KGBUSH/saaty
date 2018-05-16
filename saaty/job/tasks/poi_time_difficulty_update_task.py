# -*- coding: utf-8 -*-

from core.mq.decorators import task
from core import mq_consumer
from core import mq_producer
from core import sentry
from saaty.services.load_data_service.load_poi_time_service \
    import load_poi_time_supplier_data

__all__ = [
    'update_poi_supplier_pickup_time_data'
]


@task(consumer=mq_consumer, producer=mq_producer,
      topic='update_poi_supplier_pickup_time_data')
def update_poi_supplier_pickup_time_data():
    try:
        load_poi_time_supplier_data()

    except:
        sentry.captureException()
