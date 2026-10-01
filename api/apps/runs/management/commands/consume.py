"""
RabbitMQ consumer: reads treadmill data, saves samples in batches,
runs watchdog on stale runs and offline devices, requeues stuck analyses.
"""
import logging
import time

import pika
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.runs.controllers.telemetry import TelemetryController
from apps.runs.services import telemetry_service

logger = logging.getLogger("apps.runs.consume")

PREFETCH = 1000                         # max unacked messages from RabbitMQ
REPORT_EVERY_S = 10                     # log throughput
WATCH_EVERY_S = 10                      # run watchdog check
REQUEUE_EVERY_S = 300                   # resend stuck analyses every 5 min
INACTIVITY_TIMEOUT_S = 0.5              # timeout for polling on queue


def declare_topology(channel):
    """Create exchange, queue, bindings, and status queue."""
    channel.exchange_declare(settings.TELEMETRY_EXCHANGE, exchange_type="topic", durable=True)
    channel.queue_declare(settings.TELEMETRY_QUEUE, durable=True)
    channel.queue_bind(settings.TELEMETRY_QUEUE, settings.TELEMETRY_EXCHANGE, routing_key="#")
    channel.queue_declare(settings.DEVICE_STATUS_QUEUE, durable=True)


class Command(BaseCommand):
    help = "Consume treadmill telemetry from RabbitMQ, store it and watch live runs and devices."

    def handle(self, *args, **options):
        consumer = TelemetryController()

        params = pika.URLParameters(settings.RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        declare_topology(channel)
        channel.basic_qos(prefetch_count=PREFETCH)
        self.stdout.write(f"Consuming '{settings.TELEMETRY_QUEUE}' from {params.host}:{params.port}. Ctrl+C to stop.")

        last_tag = None
        processed = 0
        report_from = time.monotonic()
        watched_at = time.monotonic()
        requeued_at = time.monotonic()
        try:
            for method, _properties, body in channel.consume(
                settings.TELEMETRY_QUEUE, inactivity_timeout=INACTIVITY_TIMEOUT_S
            ):
                # ---- consume and buffer messages
                if method is not None:
                    consumer.handle(method.routing_key, body)
                    last_tag = method.delivery_tag
                    processed += 1
                else:
                    consumer.flush_if_due()
                if last_tag is not None and not consumer.buffer:
                    channel.basic_ack(last_tag, multiple=True)
                    last_tag = None

                # ---- watchdog: close stale runs, alert on silent devices
                if time.monotonic() - watched_at >= WATCH_EVERY_S:
                    consumer.flush()
                    if last_tag is not None:
                        channel.basic_ack(last_tag, multiple=True)
                        last_tag = None
                    watch_result = telemetry_service.run_watchdog()
                    if any(watch_result.values()):
                        logger.info("Watchdog: %s", watch_result)
                    watched_at = time.monotonic()

                # ---- requeue: re-enqueue stuck analysis tasks
                if time.monotonic() - requeued_at >= REQUEUE_EVERY_S:
                    runs = telemetry_service.requeue_stuck_analyses()
                    if runs:
                        logger.info("Requeued %s stuck run analyses.", runs)
                    requeued_at = time.monotonic()

                # ---- reporting: log throughput
                elapsed = time.monotonic() - report_from
                if elapsed >= REPORT_EVERY_S:
                    if processed:
                        logger.info("Processed %s messages (%.0f/s).", processed, processed / elapsed)
                    processed = 0
                    report_from = time.monotonic()
        except KeyboardInterrupt:
            consumer.flush()
            if last_tag is not None:
                channel.basic_ack(last_tag, multiple=True)
        finally:
            if connection.is_open:
                channel.cancel()
                connection.close()
