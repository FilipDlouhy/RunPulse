"""
Parse and route treadmill messages: batch samples/heartbeats, start/end runs.
Rejects invalid or unknown messages to dead-letter.
"""
import json
import logging
import time

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import OperationalError
from rest_framework import serializers

from apps.runs.dtos import (
    HeartbeatMessageSerializer,
    RunEndMessageSerializer,
    RunStartMessageSerializer,
    SampleMessageSerializer,
)
from apps.runs.services import alarm_monitor, telemetry_service
from common.exceptions import ApplicationError

logger = logging.getLogger(__name__)

BATCH_SIZE = 500                        # flush when buffer reaches this
MAX_WAIT_S = 1.0                        # flush if no new message for this long


def _error_text(error):
    if isinstance(error, ApplicationError):
        data = error.to_data()
    else:
        data = error.message_dict
    return json.dumps(data, ensure_ascii=False)


class TelemetryController:
    """Buffers and validates treadmill telemetry; batch-processes heartbeats and samples."""
    def __init__(self):
        self.buffer = []
        self.buffer_started_at = None
        self.run_start_serializer = RunStartMessageSerializer()
        self.sample_serializer = SampleMessageSerializer()
        self.heartbeat_serializer = HeartbeatMessageSerializer()
        self.run_end_serializer = RunEndMessageSerializer()

    def handle(self, routing_key, body):
        message = self._validate(routing_key, body)
        if message is None:
            return

        if routing_key == "sample" or routing_key == "heartbeat":
            self._add_to_buffer(routing_key, message, body)
            return

        self.flush()
        if routing_key == "run_start":
            self._start_run(message, body)
        if routing_key == "run_end":
            self._end_run(message, body)

    def flush_if_due(self):
        if self.buffer and time.monotonic() - self.buffer_started_at >= MAX_WAIT_S:
            self.flush()

    def flush(self):
        """Save heartbeats and samples in batch; reject unknown runs/devices; check alarms."""
        if not self.buffer:
            return
        batch = self.buffer
        self.buffer = []
        self.buffer_started_at = None

        heartbeats = []
        samples = []
        for routing_key, message, _body in batch:
            if routing_key == "heartbeat":
                heartbeats.append(message)
            if routing_key == "sample":
                samples.append(message)
        unknown_devices = telemetry_service.record_heartbeats(heartbeats=heartbeats)
        unknown_runs, live_runs = telemetry_service.save_samples(samples=samples)

        known_heartbeats = []
        live_samples = []
        for routing_key, message, body in batch:
            if routing_key == "heartbeat":
                if message["device"] in unknown_devices:
                    self._reject(routing_key, body, f"Unknown treadmill {message['device']}.", message["device"])
                else:
                    known_heartbeats.append(message)
            if routing_key == "sample":
                if message["run_uuid"] in unknown_runs:
                    self._reject(routing_key, body, f"Unknown run {message['run_uuid']}.", message["device"])
                elif message["run_uuid"] in live_runs:
                    live_samples.append(message)

        try:
            alarm_monitor.check_samples(live_samples)
            alarm_monitor.check_heartbeats(known_heartbeats)
        except Exception:
            logger.exception("Alarm check failed.")

    def _validate(self, routing_key, body):
        if routing_key == "run_start":
            serializer = self.run_start_serializer
        elif routing_key == "sample":
            serializer = self.sample_serializer
        elif routing_key == "heartbeat":
            serializer = self.heartbeat_serializer
        elif routing_key == "run_end":
            serializer = self.run_end_serializer
        else:
            self._reject(routing_key, body, f"Unknown message type {routing_key!r}.")
            return None

        try:
            data = json.loads(body)
        except ValueError as error:
            self._reject(routing_key, body, f"Invalid JSON: {error}")
            return None
        if not isinstance(data, dict):
            self._reject(routing_key, body, "The message must be a JSON object.")
            return None

        device = data.get("device")
        if not isinstance(device, str):
            device = ""
        try:
            return serializer.run_validation(data)
        except serializers.ValidationError as error:
            self._reject(routing_key, body, json.dumps(error.detail, ensure_ascii=False), device)
            return None

    def _add_to_buffer(self, routing_key, message, body):
        if not self.buffer:
            self.buffer_started_at = time.monotonic()
        self.buffer.append((routing_key, message, body))
        if len(self.buffer) >= BATCH_SIZE:
            self.flush()
        else:
            self.flush_if_due()

    def _start_run(self, message, body):
        try:
            telemetry_service.start_run(
                device=message["device"],
                user=message["user"],
                run_uuid=message["run_uuid"],
                run_type=message["run_type"],
                ts=message["ts"],
            )
        except (ApplicationError, DjangoValidationError) as error:
            self._reject("run_start", body, _error_text(error), message["device"])
        except OperationalError:
            raise
        except Exception as error:
            logger.exception("Unexpected error in run_start.")
            self._reject("run_start", body, f"Unexpected error: {error}", message["device"])

    def _end_run(self, message, body):
        try:
            telemetry_service.end_run(
                device=message["device"],
                run_uuid=message["run_uuid"],
                ts=message["ts"],
            )
        except (ApplicationError, DjangoValidationError) as error:
            self._reject("run_end", body, _error_text(error), message["device"])
        except OperationalError:
            raise
        except Exception as error:
            logger.exception("Unexpected error in run_end.")
            self._reject("run_end", body, f"Unexpected error: {error}", message["device"])
        alarm_monitor.forget(message["run_uuid"])

    def _reject(self, routing_key, body, error, device=""):
        """Save invalid message to dead-letter for manual inspection."""
        telemetry_service.dead_letter(routing_key=routing_key, body=body, error=error, device_serial=device)
