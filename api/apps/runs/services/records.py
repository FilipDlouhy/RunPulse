from datetime import datetime, time, timedelta

from django.utils import timezone

from apps.runs.models import RecordDistance, Run
from common.dates import week_start


def zero_if_none(value):
    if value is None:
        return 0
    return value


class RecordService:
    def __init__(self, *, personal_record_repository, run_repository):
        self.personal_record_repository = personal_record_repository
        self.run_repository = run_repository

    def new_records(self, *, run):
        if run.status != Run.Status.DONE:
            return []
        earlier = self.personal_record_repository.best_times_of_user_before(run.user_id, run.started_at)
        new = []
        for record in self.personal_record_repository.list_of_run(run):
            if record.distance not in earlier or record.time_s < earlier[record.distance]:
                new.append(record)
        return new

    def best_records(self, *, user):
        fastest_first = self.personal_record_repository.list_of_user_with_run(user)
        best = {}
        for record in fastest_first:
            if record.distance not in best:
                best[record.distance] = record

        records = []
        for distance in RecordDistance.values:
            if distance in best:
                records.append(best[distance])
        return records

    def weekly_stats(self, *, user, weeks):
        today = timezone.localdate()
        first_week = week_start(today) - timedelta(weeks=weeks - 1)
        start = timezone.make_aware(datetime.combine(first_week, time.min))
        totals = {}
        for row in self.run_repository.weekly_totals_of_user_since(user, start):
            totals[row["week"].date()] = row
        stats = []
        for index in range(weeks):
            week = first_week + timedelta(weeks=index)
            row = totals.get(week)
            if row is None:
                row = {"runs": 0, "distance_m": 0, "duration_s": 0, "trimp": 0}
            stats.append({
                "week": week,
                "runs": row["runs"],
                "km": round(zero_if_none(row["distance_m"]) / 1000, 1),
                "duration_s": zero_if_none(row["duration_s"]),
                "trimp": zero_if_none(row["trimp"]),
            })
        return stats
