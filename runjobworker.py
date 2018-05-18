# -*- coding: utf-8 -*-

import core
from core import mq_consumer
from job.tasks import tasks

app = core.setup(register_name='saaty-job-worker')

for task in tasks:
    task.consume()

mq_consumer.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=app.debug)

