# -*- coding: utf-8 -*-

from core.tasks import Task

<<<<<<< HEAD
__all__ = [
    'task',
]


def task(consumer=None, producer=None, topic=None, async=True):
=======

def task(consumer=None, producer=None, topic=None):
>>>>>>> [add] add jobs
    """
    消息队列任务装饰器
    :param consumer: 消费者客户端
    :param producer: 生产者客户端
    :param topic: topic / queue_name / exchange_name
<<<<<<< HEAD
    :param async: 是否在异步线程池消费
=======
>>>>>>> [add] add jobs
    """

    def inner_task(func):
        return Task(
            func=func,
            consumer=consumer,
            producer=producer,
            topic=topic,
<<<<<<< HEAD
            async=async,
=======
>>>>>>> [add] add jobs
        )

    return inner_task
