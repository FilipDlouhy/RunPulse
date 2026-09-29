import json

import pika

EXCHANGE = "telemetry"
QUEUE = "telemetry"
STATUS_QUEUE = "device_status"
PROPERTIES = pika.BasicProperties(content_type="application/json", delivery_mode=pika.DeliveryMode.Persistent)


class Publisher:
    def __init__(self, url):
        self.connection = pika.BlockingConnection(pika.URLParameters(url))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(EXCHANGE, exchange_type="topic", durable=True)
        self.channel.queue_declare(QUEUE, durable=True)
        self.channel.queue_bind(QUEUE, EXCHANGE, routing_key="#")
        self.channel.queue_declare(STATUS_QUEUE, durable=True)
        self.sent = 0

    def publish(self, message):
        self.channel.basic_publish(EXCHANGE, message["type"], json.dumps(message), PROPERTIES)
        self.sent += 1

    def device_statuses(self):
        statuses = []
        while True:
            method, _properties, body = self.channel.basic_get(STATUS_QUEUE, auto_ack=True)
            if method is None:
                return statuses
            statuses.append(json.loads(body))

    def sleep(self, seconds):
        self.connection.sleep(seconds)

    def close(self):
        if self.connection.is_open:
            self.connection.close()
