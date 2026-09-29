from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.runners.calculations import heart_rate_limits, karvonen_zones
from apps.runs.dtos import LiveRunState
from apps.runs.live import live_metrics, live_sample
from apps.runs.models import RunType
from common.exceptions import ConflictError, NotFoundError

LIVE_HISTORY = timedelta(minutes=10)


class RunService:
    def __init__(
        self,
        *,
        run_repository,
        sample_repository,
        runner_profile_repository,
        telemetry_service,
        alert_service,
        record_service,
    ):
        self.run_repository = run_repository
        self.sample_repository = sample_repository
        self.runner_profile_repository = runner_profile_repository
        self.telemetry_service = telemetry_service
        self.alert_service = alert_service
        self.record_service = record_service

    def list_runs(self, *, user, run_type=None):
        if run_type in RunType.values:
            run_types = [run_type]
        else:
            run_types = None
        return self.run_repository.list_finished_of_user_with_summary(user, run_types=run_types)

    def get_run(self, *, user, run_id):
        run = self.run_repository.get_of_user_with_summary(user, run_id)
        self._check_found(run)
        run.new_records = self.record_service.new_records(run=run)
        return run

    @transaction.atomic
    def update_run(self, *, user, run_id, rpe):
        run = self.run_repository.get_of_user_for_update(user, run_id)
        self._check_found(run)
        run.rpe = rpe
        self.run_repository.save(run, update_fields=["rpe"])
        return self.get_run(user=user, run_id=run_id)

    def list_samples(self, *, user, run_id, step):
        run = self.run_repository.get_of_user(user, run_id)
        self._check_found(run)
        points = self.sample_repository.bucketed_of_run(run, step)
        for point in points:
            point["t"] = int(point["bucket"]) * step
        return points

    @transaction.atomic
    def stop_run(self, *, user, run_id):
        run = self.run_repository.get_of_user_with_device_for_update(user, run_id)
        self._check_found(run)
        if not run.is_live:
            raise ConflictError("The run is no longer live.")
        end_time = self.sample_repository.last_time_of_run(run)
        if end_time is None:
            end_time = timezone.now()
        self.telemetry_service.close_run(run=run, ts=end_time)
        return self.get_run(user=user, run_id=run_id)

    @transaction.atomic
    def stop_runs_on_device(self, *, device):
        for run in self.run_repository.list_live_on_device_for_update(device):
            end_time = self.sample_repository.last_time_of_run(run)
            if end_time is None:
                end_time = timezone.now()
            self.telemetry_service.close_run(run=run, ts=end_time)

    def current_live_run(self, *, user):
        run = self.run_repository.get_current_live_with_summary(user)
        if run is None:
            return None
        recent = self.sample_repository.list_of_run_since(run, timezone.now() - LIVE_HISTORY)
        samples = []
        for sample in recent:
            point = live_sample(
                started_at=run.started_at,
                seq=sample.seq,
                ts=sample.time,
                hr=sample.hr,
                speed_kmh=sample.speed_kmh,
            )
            samples.append(point)
        return LiveRunState(
            run=run,
            metrics=self._live_metrics(run),
            samples=samples,
            alerts=self.alert_service.open_for_run(run=run),
        )

    def _check_found(self, run):
        if run is None:
            raise NotFoundError("Run not found.")

    def _live_metrics(self, run):
        last = self.sample_repository.get_last_of_run(run)
        if last is None:
            return None
        profile = self.runner_profile_repository.get_by_user(run.user_id)
        hr_rest, hr_max = heart_rate_limits(profile, timezone.localdate())
        return live_metrics(
            started_at=run.started_at,
            ts=last.time,
            hr=last.hr,
            speed_kmh=last.speed_kmh,
            incline=last.incline,
            zones=karvonen_zones(hr_rest, hr_max),
            distance_m=self.sample_repository.distance_m_of_run(run),
        )
