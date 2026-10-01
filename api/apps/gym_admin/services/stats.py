"""
Gym operational statistics: real-time treadmill status, usage heatmaps, and run counts.
"""
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from apps.gym_admin.dtos import GymHeatmap, GymOverview
from apps.gym_admin.models import Device

PRAGUE_TZ = ZoneInfo("Europe/Prague")


class GymStatsService:
    """Collects and aggregates gym equipment usage and alert statistics."""

    def __init__(self, *, device_repository, run_repository, usage_hourly_repository, alert_service):
        self.device_repository = device_repository
        self.run_repository = run_repository
        self.usage_hourly_repository = usage_hourly_repository
        self.alert_service = alert_service

    def overview(self):
        now = timezone.now()
        treadmills = self.device_repository.get_all()
        in_use = 0
        out_of_order = 0
        offline = 0
        for treadmill in treadmills:
            if treadmill.status == Device.Status.IN_USE:
                in_use += 1
            if treadmill.status == Device.Status.OUT_OF_ORDER:
                out_of_order += 1
            if treadmill.status == Device.Status.OFFLINE:
                offline += 1

        day_start = timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)
        return GymOverview(
            treadmills_total=len(treadmills),
            treadmills_in_use=in_use,
            treadmills_free=len(treadmills) - in_use - out_of_order - offline,
            treadmills_out_of_order=out_of_order,
            treadmills_offline=offline,
            runs_today=self.run_repository.count_started_since(day_start),
            alerts=self.alert_service.open_alerts(),
        )

    def heatmap(self, *, weeks):
        now = timezone.now()
        since = now - timedelta(weeks=weeks)
        rows = self.usage_hourly_repository.seconds_by_weekday_hour(since=since, until=now, tz=PRAGUE_TZ)

        heatmap = []
        for _day in range(7):
            heatmap.append([0.0] * 24)
        for row in rows:
            day = row["weekday"] - 1
            hour = row["hour"]
            heatmap[day][hour] = round(row["total_seconds"] / 3600 / weeks, 2)
        return GymHeatmap(weeks=weeks, heatmap=heatmap)
