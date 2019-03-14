# -*- coding: utf-8 -*-

import os; os.environ['APP_REGISTER_NAME'] = 'saaty-job-worker'

import core
from core import mq_consumer
from job.tasks import tasks

app = core.setup()

for task in tasks:
    task.consume()

mq_consumer.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=app.debug)
