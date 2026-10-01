from dataclasses import dataclass

from rest_framework import serializers


@dataclass(frozen=True)
class TechOverview:
    """Tech dashboard data: queue stats, pipeline stats, dead letters, slowest steps."""
    queue: dict | None
    queue_error: str
    dead_letter_count: int
    dead_letters: list
    pipeline_count: int
    pipeline_failed: int
    pipeline_avg_ms: int | None
    slowest_steps: list
    pipelines: list


class QueueStatsResponseSerializer(serializers.Serializer):
    messages = serializers.IntegerField()
    ready = serializers.IntegerField()
    unacked = serializers.IntegerField()
    consumers = serializers.IntegerField()
    publish_rate = serializers.FloatField()
    deliver_rate = serializers.FloatField()


class DeadLetterResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    routing_key = serializers.CharField()
    device_serial = serializers.CharField()
    body = serializers.CharField(source="redacted_body")
    error = serializers.CharField()
    created_at = serializers.DateTimeField()


class SlowStepResponseSerializer(serializers.Serializer):
    name = serializers.CharField()
    avg_ms = serializers.FloatField()
    max_ms = serializers.IntegerField()
    count = serializers.IntegerField()


class PipelineStepResponseSerializer(serializers.Serializer):
    order = serializers.IntegerField()
    name = serializers.CharField()
    status = serializers.CharField()
    duration_ms = serializers.IntegerField(allow_null=True)
    error = serializers.CharField()


class PipelineRunResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    status = serializers.CharField()
    run_id = serializers.IntegerField(allow_null=True)
    device = serializers.CharField(source="run.device.serial", allow_null=True)
    started_at = serializers.DateTimeField()
    finished_at = serializers.DateTimeField(allow_null=True)
    duration_ms = serializers.IntegerField(allow_null=True)
    failed_step = serializers.CharField()
    steps = PipelineStepResponseSerializer(many=True, source="steps.all")


class TechOverviewResponseSerializer(serializers.Serializer):
    queue = QueueStatsResponseSerializer(allow_null=True)
    queue_error = serializers.CharField()
    dead_letter_count = serializers.IntegerField()
    dead_letters = DeadLetterResponseSerializer(many=True)
    pipeline_count = serializers.IntegerField()
    pipeline_failed = serializers.IntegerField()
    pipeline_avg_ms = serializers.IntegerField(allow_null=True)
    slowest_steps = SlowStepResponseSerializer(many=True)
    pipelines = PipelineRunResponseSerializer(many=True)
