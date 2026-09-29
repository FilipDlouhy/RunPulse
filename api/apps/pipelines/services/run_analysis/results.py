from django.db import transaction
from django.utils import timezone

from apps.realtime.notify import notify_devices_changed, notify_run_status
from apps.runs.models import PersonalRecord, Run, RunSummary
from common.exceptions import NotFoundError


class AnalysisService:
    def __init__(self, *, run_repository, run_summary_repository, personal_record_repository, device_repository):
        self.run_repository = run_repository
        self.run_summary_repository = run_summary_repository
        self.personal_record_repository = personal_record_repository
        self.device_repository = device_repository

    def can_analyze(self, *, run_id):
        return self.run_repository.get_analyzing_by_id(run_id) is not None

    @transaction.atomic
    def save_result(self, *, run_id, summary, records, device_hours):
        run = self.run_repository.get_by_id_for_update(run_id)
        if run is None or run.is_live:
            raise NotFoundError(f"Run {run_id} cannot be analyzed.")

        row = self.run_summary_repository.get_by_run(run)
        first_analysis = row is None
        if first_analysis:
            row = RunSummary(run=run)
        row.distance_m = summary["distance_m"]
        row.duration_s = summary["duration_s"]
        row.avg_pace_s = summary["avg_pace_s"]
        row.avg_hr = summary["avg_hr"]
        row.max_hr = summary["max_hr"]
        row.zones = summary["zones"]
        row.splits = summary["splits"]
        row.trimp = summary["trimp"]
        row.kcal = summary["kcal"]
        row.cleaned_points = summary["cleaned_points"]
        row.analyzed_at = timezone.now()
        self.run_summary_repository.save(row)

        earlier = self.personal_record_repository.best_times_of_user_before(run.user_id, run.started_at)
        new_records = []
        for distance, time_s in records.items():
            record = PersonalRecord(
                user_id=run.user_id,
                run=run,
                distance=distance,
                time_s=time_s,
                achieved_at=run.started_at,
            )
            new_records.append(record)
        self.personal_record_repository.replace_of_run(run, new_records)

        if first_analysis:
            self._add_device_usage(run.device_id, device_hours)

        run.finish_analysis()
        self.run_repository.save(run, update_fields=["status"])

        new_count = 0
        for distance, time_s in records.items():
            if distance not in earlier or time_s < earlier[distance]:
                new_count += 1
        notify_run_status(run.user_id, run.pk, Run.Status.DONE, new_count)
        return run

    def _add_device_usage(self, device_id, hours):
        device = self.device_repository.get_by_id_for_update(device_id)
        needed_service = device.needs_service
        device.add_usage(hours)
        self.device_repository.save(device, update_fields=["total_hours", "hours_since_service", "needs_service"])
        if device.needs_service and not needed_service:
            notify_devices_changed()

    @transaction.atomic
    def mark_failed(self, *, run_id):
        run = self.run_repository.get_by_id_for_update(run_id)
        if run is None or run.is_live:
            return None
        run.fail_analysis()
        self.run_repository.save(run, update_fields=["status"])
        notify_run_status(run.user_id, run.pk, Run.Status.FAILED)
        return run
