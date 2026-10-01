import logging
from datetime import timedelta

import httpx
from django.db import transaction
from django.utils import timezone

from apps.pipelines.dtos import TechOverview
from apps.pipelines.rabbitmq import fetch_queue_stats
from apps.runs.messaging import republish_telemetry
from common.exceptions import ConflictError, NotFoundError

logger = logging.getLogger(__name__)

TECH_WINDOW = timedelta(hours=24)   # time window for pipeline/step stats
RECENT_DEAD_LETTERS = 50            # show last N dead letters
RECENT_PIPELINES = 30               # show last N pipeline runs
SLOWEST_STEPS = 5                   # show N slowest steps


class TechService:
    """Collect and expose tech/operational metrics: queue, pipeline stats, dead letters."""
    def __init__(self, *, dead_letter_repository, pipeline_run_repository, pipeline_step_repository):
        self.dead_letter_repository = dead_letter_repository
        self.pipeline_run_repository = pipeline_run_repository
        self.pipeline_step_repository = pipeline_step_repository

    def overview(self):
        """Collect queue stats, pipeline stats, dead letters, and slowest steps."""
        queue, queue_error = self._queue()
        since = timezone.now() - TECH_WINDOW
        stats = self.pipeline_run_repository.stats_since(since)

        pipeline_avg_ms = None
        if stats["avg_duration"] is not None:
            pipeline_avg_ms = round(stats["avg_duration"].total_seconds() * 1000)

        return TechOverview(
            queue=queue,
            queue_error=queue_error,
            dead_letter_count=self.dead_letter_repository.count(),
            dead_letters=self.dead_letter_repository.list_recent(RECENT_DEAD_LETTERS),
            pipeline_count=stats["total"],
            pipeline_failed=stats["failed"],
            pipeline_avg_ms=pipeline_avg_ms,
            slowest_steps=self.pipeline_step_repository.slowest_since(since, SLOWEST_STEPS),
            pipelines=self.pipeline_run_repository.list_recent_with_steps_since(since, RECENT_PIPELINES),
        )

    @transaction.atomic
    def retry_dead_letter(self, *, dead_letter_id):
        """Republish a dead-lettered message and remove it from the DLQ."""
        dead_letter = self.dead_letter_repository.get_by_id_for_update(dead_letter_id)
        if dead_letter is None:
            raise NotFoundError("Dead letter not found.")
        if not dead_letter.routing_key:
            raise ConflictError("The dead letter has no routing key.")
        republish_telemetry(dead_letter.routing_key, dead_letter.body)
        self.dead_letter_repository.delete(dead_letter)

    def _queue(self):
        """Fetch RabbitMQ queue stats; return (stats, error_message) tuple."""
        try:
            queue = fetch_queue_stats()
            return queue, ""
        except (httpx.HTTPError, ValueError) as error:
            logger.warning("RabbitMQ management API failed: %s", error)
            return None, "RabbitMQ management API is not reachable."
