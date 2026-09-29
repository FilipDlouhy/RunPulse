from dataclasses import dataclass

from rest_framework import serializers

from .models import Run, RunType


@dataclass(frozen=True)
class LiveRunState:
    run: Run
    metrics: dict | None
    samples: list
    alerts: list


class RunStartMessageSerializer(serializers.Serializer):
    device = serializers.CharField(max_length=40)
    user = serializers.CharField(max_length=150)
    run_uuid = serializers.UUIDField()
    run_type = serializers.ChoiceField(choices=RunType.choices)
    ts = serializers.DateTimeField()


class SampleMessageSerializer(serializers.Serializer):
    device = serializers.CharField(max_length=40)
    run_uuid = serializers.UUIDField()
    seq = serializers.IntegerField(min_value=0)
    ts = serializers.DateTimeField()
    hr = serializers.IntegerField(min_value=0, max_value=300, allow_null=True)
    speed_kmh = serializers.FloatField(min_value=0, max_value=30)
    incline = serializers.FloatField(min_value=-5, max_value=25)


class HeartbeatMessageSerializer(serializers.Serializer):
    device = serializers.CharField(max_length=40)
    status = serializers.ChoiceField(choices=["ok", "fault"])
    firmware = serializers.CharField(max_length=40, allow_blank=True)
    ts = serializers.DateTimeField()


class RunEndMessageSerializer(serializers.Serializer):
    device = serializers.CharField(max_length=40)
    run_uuid = serializers.UUIDField()
    ts = serializers.DateTimeField()


class RunSummaryBriefResponseSerializer(serializers.Serializer):
    distance_m = serializers.IntegerField()
    duration_s = serializers.IntegerField()
    avg_pace_s = serializers.IntegerField(allow_null=True)
    avg_hr = serializers.IntegerField(allow_null=True)
    trimp = serializers.IntegerField()


class RunSummaryResponseSerializer(RunSummaryBriefResponseSerializer):
    max_hr = serializers.IntegerField(allow_null=True)
    zones = serializers.ListField(child=serializers.IntegerField())
    splits = serializers.JSONField()
    kcal = serializers.IntegerField()
    cleaned_points = serializers.IntegerField()
    analyzed_at = serializers.DateTimeField()


class PersonalRecordResponseSerializer(serializers.Serializer):
    distance = serializers.CharField()
    time_s = serializers.IntegerField()
    pace_s = serializers.IntegerField()
    achieved_at = serializers.DateTimeField()
    run_id = serializers.IntegerField()


class RunListItemResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    uuid = serializers.UUIDField()
    type = serializers.CharField()
    status = serializers.CharField()
    device = serializers.CharField(source="device.serial")
    started_at = serializers.DateTimeField()
    ended_at = serializers.DateTimeField(allow_null=True)
    rpe = serializers.IntegerField(allow_null=True)
    summary = RunSummaryBriefResponseSerializer(allow_null=True)


class RunDetailResponseSerializer(RunListItemResponseSerializer):
    summary = RunSummaryResponseSerializer(allow_null=True)
    new_records = PersonalRecordResponseSerializer(many=True)


class ListRunsRequestSerializer(serializers.Serializer):
    type = serializers.CharField(required=False, allow_blank=True, source="run_type")


class UpdateRunRequestSerializer(serializers.Serializer):
    rpe = serializers.IntegerField(min_value=1, max_value=10, allow_null=True)


class ListSamplesRequestSerializer(serializers.Serializer):
    step = serializers.IntegerField(min_value=1, max_value=300, default=10)


class SamplePointResponseSerializer(serializers.Serializer):
    t = serializers.IntegerField()
    hr = serializers.FloatField(allow_null=True)
    speed_kmh = serializers.FloatField()
    incline = serializers.FloatField()


class LiveMetricsResponseSerializer(serializers.Serializer):
    elapsed_s = serializers.IntegerField()
    hr = serializers.IntegerField(allow_null=True)
    zone = serializers.IntegerField(allow_null=True)
    speed_kmh = serializers.FloatField()
    pace_s = serializers.IntegerField(allow_null=True)
    incline = serializers.FloatField()
    distance_m = serializers.IntegerField()


class LiveSampleResponseSerializer(serializers.Serializer):
    seq = serializers.IntegerField()
    t = serializers.IntegerField()
    hr = serializers.IntegerField(allow_null=True)
    speed_kmh = serializers.FloatField()


class RunAlertResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    message = serializers.CharField()
    created_at = serializers.DateTimeField()


class LiveRunResponseSerializer(serializers.Serializer):
    run = RunListItemResponseSerializer()
    metrics = LiveMetricsResponseSerializer(allow_null=True)
    samples = LiveSampleResponseSerializer(many=True)
    alerts = RunAlertResponseSerializer(many=True)


class WeeklyStatsRequestSerializer(serializers.Serializer):
    weeks = serializers.IntegerField(min_value=1, max_value=52, default=12)


class WeeklyStatResponseSerializer(serializers.Serializer):
    week = serializers.DateField()
    runs = serializers.IntegerField()
    km = serializers.FloatField()
    duration_s = serializers.IntegerField()
    trimp = serializers.IntegerField()
