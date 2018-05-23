# -*- coding: utf-8 -*-

from core.mq.decorators import task
from core import mq_consumer
from core import mq_producer
from core import sentry
from core import app
from saaty.services.load_data_service.load_time_cost_service \
    import load_time_cost_receiver_data, load_time_cost_supplier_data

__all__ = [
    'update_poi_pickup_time_cost_data',
    'update_receiver_time_cost_data'
]


@task(consumer=mq_consumer, producer=mq_producer,
      topic='job_update_pickup_time_cost_data')
def update_poi_pickup_time_cost_data():
    try:
        batch_size = app.config.get('JOB_POI_TIME_DIFFICULT_UPDATE_BATCH_SIZE',
                                    2000)
        load_time_cost_supplier_data(batch_size=batch_size)
    except:
        sentry.captureException()


@task(consumer=mq_consumer, producer=mq_producer,
      topic='job_update_receiver_time_cost_data')
def update_receiver_time_cost_data():
    try:
        batch_size = app.config.get('JOB_POI_TIME_DIFFICULT_UPDATE_BATCH_SIZE',
                                    2000)
        load_time_cost_receiver_data(batch_size=batch_size)
    except:
        sentry.captureException()
