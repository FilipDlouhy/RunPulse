import time
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from apps.gym_admin.models import Alert
from apps.realtime.notify import notify_users
from apps.runners.calculations import heart_rate_limits, karvonen_zones
from apps.runs.live import live_metrics, live_sample
from apps.runs.models import Run

MAX_MESSAGE_AGE = timedelta(minutes=2)
CACHE_TTL_S = 60
SAMPLES_THROTTLE_S = 1.0


@dataclass
class RunWatch:
    run: Run
    distance_m: float
    hr_max: int = 0
    zones: list | None = None
    loaded_at: float = 0.0
    last_seq: int = -1
    last_sample: dict | None = None
    samples_sent_at: float | None = None
    high_since: datetime | None = None
    missing_since: datetime | None = None
    high_raised: bool = False
    missing_raised: bool = False

    @property
    def serial(self):
        return self.run.device.serial


class AlarmMonitor:
    def __init__(
        self,
        *,
        run_repository,
        sample_repository,
        device_repository,
        runner_profile_repository,
        alert_service,
    ):
        self.run_repository = run_repository
        self.sample_repository = sample_repository
        self.device_repository = device_repository
        self.runner_profile_repository = runner_profile_repository
        self.alert_service = alert_service
        self.watches = {}

    def check_samples(self, samples):
        oldest_allowed = timezone.now() - MAX_MESSAGE_AGE
        samples_by_run = {}
        for sample in samples:
            if sample["ts"] < oldest_allowed:
                continue
            run_uuid = sample["run_uuid"]
            if run_uuid not in samples_by_run:
                samples_by_run[run_uuid] = []
            samples_by_run[run_uuid].append(sample)

        updates = []
        for run_uuid, run_samples in samples_by_run.items():
            run_samples.sort(key=lambda sample: sample["seq"])
            watch = self._watch(run_uuid, first_seq=run_samples[0]["seq"])
            if watch is None:
                continue

            accepted = []
            for sample in run_samples:
                if sample["seq"] <= watch.last_seq:
                    continue
                watch.last_seq = sample["seq"]
                watch.distance_m += sample["speed_kmh"] / 3.6
                watch.last_sample = sample
                accepted.append(sample)
                self._check_sample(watch, sample)

            if accepted and self._samples_due(watch):
                event = self._samples_event(watch, accepted)
                updates.append((watch.run.user_id, event))
        notify_users(updates)

    def check_heartbeats(self, heartbeats):
        oldest_allowed = timezone.now() - MAX_MESSAGE_AGE
        for heartbeat in heartbeats:
            if heartbeat["status"] != "fault":
                continue
            if heartbeat["ts"] < oldest_allowed:
                continue
            device = self.device_repository.get_by_serial(heartbeat["device"])
            if device is None:
                continue
            self.alert_service.raise_alert(
                device=device,
                alert_type=Alert.Type.DEVICE_FAULT,
                message=f"{device.serial}: treadmill reports a fault",
            )

    def forget(self, run_uuid):
        if run_uuid in self.watches:
            del self.watches[run_uuid]

    def _check_sample(self, watch, sample):
        if sample["hr"] is None:
            watch.high_since = None
            watch.high_raised = False
            self._check_missing_hr(watch, sample["ts"])
        else:
            watch.missing_since = None
            watch.missing_raised = False
            self._check_high_hr(watch, sample["hr"], sample["ts"])

    def _check_missing_hr(self, watch, ts):
        if watch.missing_since is None:
            watch.missing_since = ts
        if watch.missing_raised:
            return
        missing_s = (ts - watch.missing_since).total_seconds()
        if missing_s < settings.NO_DATA_SECONDS:
            return
        watch.missing_raised = True
        self._raise(
            watch,
            Alert.Type.NO_HR,
            f"{watch.serial}: no heart rate for over {settings.NO_DATA_SECONDS} s",
        )

    def _check_high_hr(self, watch, hr, ts):
        if hr * 100 < watch.hr_max * settings.HR_ALARM_PCT:
            watch.high_since = None
            watch.high_raised = False
            return

        if watch.high_since is None:
            watch.high_since = ts
        if watch.high_raised:
            return
        high_s = (ts - watch.high_since).total_seconds()
        if high_s < settings.HR_ALARM_SECONDS:
            return
        watch.high_raised = True
        percent = round(hr * 100 / watch.hr_max)
        self._raise(
            watch,
            Alert.Type.HR_HIGH,
            f"{watch.serial}: heart rate at {percent}% of max for over {settings.HR_ALARM_SECONDS} s",
        )

    def _raise(self, watch, alert_type, message):
        self.alert_service.raise_alert(device=watch.run.device, run=watch.run, alert_type=alert_type, message=message)

    def _samples_due(self, watch):
        now = time.monotonic()
        if watch.samples_sent_at is not None and now - watch.samples_sent_at < SAMPLES_THROTTLE_S:
            return False
        watch.samples_sent_at = now
        return True

    def _samples_event(self, watch, accepted):
        started_at = watch.run.started_at
        last = watch.last_sample
        metrics = live_metrics(
            started_at=started_at,
            ts=last["ts"],
            hr=last["hr"],
            speed_kmh=last["speed_kmh"],
            incline=last["incline"],
            zones=watch.zones,
            distance_m=watch.distance_m,
        )
        points = []
        for sample in accepted:
            point = live_sample(
                started_at=started_at,
                seq=sample["seq"],
                ts=sample["ts"],
                hr=sample["hr"],
                speed_kmh=sample["speed_kmh"],
            )
            points.append(point)
        return {
            "type": "samples",
            "run_id": watch.run.pk,
            "metrics": metrics,
            "samples": points,
        }

    def _watch(self, run_uuid, *, first_seq):
        watch = self.watches.get(run_uuid)
        if watch is not None and time.monotonic() - watch.loaded_at < CACHE_TTL_S:
            return watch

        run = self.run_repository.get_live_by_uuid_with_device(run_uuid)
        if run is None:
            self.forget(run_uuid)
            return None
        if watch is None:
            distance_m = self.sample_repository.distance_m_before(run, first_seq)
            watch = RunWatch(run=run, distance_m=distance_m)
            self.watches[run_uuid] = watch

        profile = self.runner_profile_repository.get_by_user(run.user_id)
        hr_rest, hr_max = heart_rate_limits(profile, timezone.localdate())
        watch.run = run
        watch.hr_max = hr_max
        watch.zones = karvonen_zones(hr_rest, hr_max)
        watch.loaded_at = time.monotonic()
        return watch
