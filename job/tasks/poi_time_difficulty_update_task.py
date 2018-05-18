# -*- coding: utf-8 -*-

from core.mq.decorators import task
from core import mq_consumer
from core import mq_producer
from core import sentry
from core import app
from saaty.services.load_data_service.load_poi_time_service \
    import load_poi_time_supplier_data

__all__ = [
    'update_poi_supplier_pickup_time_data'
]


@task(consumer=mq_consumer, producer=mq_producer,
      topic='job_update_poi_supplier_pickup_time_data')
def update_poi_supplier_pickup_time_data():

    try:
        batch_size = app.config.get('JOB_POI_TIME_DIFFICULT_UPDATE_BATCH_SIZE',
                                    2000)
        load_poi_time_supplier_data(batch_size=batch_size)
    except:
        sentry.captureException()
