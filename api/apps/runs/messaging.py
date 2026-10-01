"""
Publish from the API to RabbitMQ: retried dead letters and treadmill status for the simulator.
"""
import json

import pika
from django.conf import settings
from pika.exceptions import AMQPError

from common.exceptions import ServiceUnavailableError

JSON_PROPERTIES = pika.BasicProperties(content_type="application/json", delivery_mode=2)


def publish(exchange, routing_key, body, *, unroutable_message):
    """Send message with mandatory flag; raises if no queue is bound to the routing key."""
    try:
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
    except AMQPError as error:
        raise ServiceUnavailableError("RabbitMQ is not available.") from error
    try:
        channel = connection.channel()
        channel.confirm_delivery()
        channel.basic_publish(exchange, routing_key, body, properties=JSON_PROPERTIES, mandatory=True)
    except AMQPError as error:
        raise ServiceUnavailableError(unroutable_message) from error
    finally:
        if connection.is_open:
            connection.close()


def republish_telemetry(routing_key, body):
    publish(
        settings.TELEMETRY_EXCHANGE,
        routing_key,
        body.encode(),
        unroutable_message="The telemetry queue does not exist.",
    )


def send_device_status(serial, status):
    body = json.dumps({"device": serial, "status": status})
    publish(
        "",
        settings.DEVICE_STATUS_QUEUE,
        body.encode(),
        unroutable_message="The device status queue does not exist.",
    )
