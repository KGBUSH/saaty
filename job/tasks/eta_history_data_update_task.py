# -*- coding: utf-8 -*-

from core.mq.decorators import task
from core import mq_consumer
from core import mq_producer
from core import sentry
from core import app
from saaty.services.load_data_service.load_eta_history_service \
    import load_supplier_history_data, load_transporter_history_data, load_poi_statistics_data, load_transporter_peak_data

__all__ = [
    'update_supplier_history_data',
    'update_transporter_history_data',
    'update_poi_statistics_data',
    'update_transporter_peak_data'
]


@task(consumer=mq_consumer, producer=mq_producer,
      topic='job_update_supplier_history_data')
def update_supplier_history_data():
    try:
        batch_size = app.config.get('JOB_POI_TIME_DIFFICULT_UPDATE_BATCH_SIZE',
                                    2000)
        load_supplier_history_data(batch_size=batch_size)
    except:
        sentry.captureException()


@task(consumer=mq_consumer, producer=mq_producer,
      topic='job_update_transporter_history_data')
def update_transporter_history_data():
    try:
        batch_size = app.config.get('JOB_POI_TIME_DIFFICULT_UPDATE_BATCH_SIZE',
                                    2000)
        load_transporter_history_data(batch_size=batch_size)
    except:
        sentry.captureException()


@task(consumer=mq_consumer, producer=mq_producer,
      topic='job_update_poi_statistics_data')
def update_poi_statistics_data():
    try:
        batch_size = app.config.get('JOB_POI_TIME_DIFFICULT_UPDATE_BATCH_SIZE',
                                    2000)
        load_poi_statistics_data(batch_size=batch_size)
    except:
        sentry.captureException()


@task(consumer=mq_consumer, producer=mq_producer,
      topic='job_update_transporter_peak_data')
def update_transporter_peak_data():
    try:
        batch_size = app.config.get('JOB_POI_TIME_DIFFICULT_UPDATE_BATCH_SIZE',
                                    2000)
        load_transporter_peak_data(batch_size=batch_size)
    except:
        sentry.captureException()
