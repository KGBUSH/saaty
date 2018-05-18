# -*- coding: utf-8 -*-

from common.framework.exceptions import ImproperlyConfigured
from core import app


class ProducerImproperlyConfigured(ImproperlyConfigured):
    message = 'producer improperly configured'


class ConsumerImproperlyConfigured(ImproperlyConfigured):
    message = 'consumer improperly configured'


class TopicImproperlyConfigured(ImproperlyConfigured):
    message = 'topic improperly configured'


class Task(object):

    def __init__(self, func, producer=None, consumer=None,
                 topic=None, async=True):
        self.func = func
        self.producer = producer
        self.consumer = consumer
        self.topic = topic
        self.async = async

    def delay(self, **kwargs):
        if self.producer is None:
            raise ProducerImproperlyConfigured()
        if self.topic is None:
            raise TopicImproperlyConfigured()
        self.producer.send(
            topic=self.topic,
            msg=kwargs,
        )

    def __call__(self, **kwargs):
        with app.app_context():
            return self.func(**kwargs)

    def as_task(self):
        def task(body, meta):
            return self(**body)
        task.__name__ = self.func.__name__
        task.__module__ = self.func.__module__
        task.__doc__ = self.func.__doc__
        return task

    def consume(self):
        if self.consumer is None:
            raise ConsumerImproperlyConfigured()
        if self.topic is None:
            raise TopicImproperlyConfigured()
        self.consumer.consume(
            queue=self.topic,
            listener=self.as_task(),
            async=self.async,
        )
