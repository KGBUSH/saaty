# -*- coding: utf-8 -*-
from common.mq.kafka_logger import BizkafkaLogger


class AlgokafkaLogger(BizkafkaLogger):

    def info(self, biz_type, data):
        self._info(biz_type, data, self.topicName)
