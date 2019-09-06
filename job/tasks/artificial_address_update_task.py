# -*- coding: utf-8 -*-

"""

@author: zhenfengjiang

@contact: zhenfengjiang@imdada.cn

@file: artificial_address_update_task.py

@time: 2019/9/6 14:24

@desc:

"""

from core.mq.decorators import task
from core import mq_consumer
from core import mq_producer
from core import sentry
from core import app
from saaty.services.load_data_service.load_artificial_address_service import \
    load_artificial_address_data


@task(consumer=mq_consumer, producer=mq_producer,
      topic='job_update_artificial_address_data')
def update_artificial_address_data():
    try:
        batch_size = app.config.get('JOB_UPDATE_ARTIFICIAL_DATA_BATCH_SIZE',
                                    2000)
        load_artificial_address_data(batch_size=batch_size)
    except:
        sentry.captureException()
