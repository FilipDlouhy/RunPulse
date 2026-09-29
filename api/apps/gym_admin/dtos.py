from dataclasses import dataclass

from rest_framework import serializers


@dataclass(frozen=True)
class GymOverview:
    treadmills_total: int
    treadmills_in_use: int
    treadmills_free: int
    treadmills_out_of_order: int
    treadmills_offline: int
    runs_today: int
    alerts: list


@dataclass(frozen=True)
class GymHeatmap:
    weeks: int
    heatmap: list


@dataclass(frozen=True)
class DemoSeed:
    manager: object
    runner: object
    member_count: int
    device_count: int


class DeviceResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    serial = serializers.CharField()
    status = serializers.CharField()
    firmware = serializers.CharField()
    last_seen = serializers.DateTimeField(allow_null=True)
    total_hours = serializers.DecimalField(max_digits=8, decimal_places=1)
    hours_since_service = serializers.DecimalField(max_digits=8, decimal_places=1)
    needs_service = serializers.BooleanField()


class AlertResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    message = serializers.CharField()
    device = serializers.CharField(source="device.serial")
    run_id = serializers.IntegerField(allow_null=True)
    created_at = serializers.DateTimeField()
    acknowledged_at = serializers.DateTimeField(allow_null=True)


class GymOverviewResponseSerializer(serializers.Serializer):
    treadmills_total = serializers.IntegerField()
    treadmills_in_use = serializers.IntegerField()
    treadmills_free = serializers.IntegerField()
    treadmills_out_of_order = serializers.IntegerField()
    treadmills_offline = serializers.IntegerField()
    runs_today = serializers.IntegerField()
    alerts = AlertResponseSerializer(many=True)


class HeatmapRequestSerializer(serializers.Serializer):
    weeks = serializers.IntegerField(min_value=1, max_value=12, default=4)


class HeatmapResponseSerializer(serializers.Serializer):
    weeks = serializers.IntegerField()
    heatmap = serializers.ListField(child=serializers.ListField(child=serializers.FloatField()))
