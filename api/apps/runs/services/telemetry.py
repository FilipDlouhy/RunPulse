"""
Store and manage treadmill telemetry: start/end runs, save samples, mark stale runs,
record heartbeats, handle watchdog alerts.
"""
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.gym_admin.models import Alert
from apps.pipelines import tasks
from apps.realtime.notify import notify_devices_changed, notify_run_status
from apps.runs.models import DeadLetter, Run, Sample
from common.exceptions import ConflictError, NotFoundError, ValidationFailedError

STALE_ENDED = "ended"
STALE_DISCARDED = "discarded"
RUN_DISCARDED = "DISCARDED"


class TelemetryService:
    """Treadmill telemetry and device lifecycle: start/end runs, save samples, watchdog."""
    def __init__(
        self,
        *,
        run_repository,
        sample_repository,
        dead_letter_repository,
        device_repository,
        user_repository,
        alert_service,
    ):
        self.run_repository = run_repository
        self.sample_repository = sample_repository
        self.dead_letter_repository = dead_letter_repository
        self.device_repository = device_repository
        self.user_repository = user_repository
        self.alert_service = alert_service

    @transaction.atomic
    def start_run(self, *, device, user, run_uuid, run_type, ts):
        run = self.run_repository.get_by_uuid(run_uuid)
        if run is not None:
            return run

        treadmill = self.device_repository.get_by_serial_for_update(device)
        if treadmill is None:
            raise NotFoundError(f"Unknown treadmill {device}.")
        if treadmill.is_out_of_order:
            raise ConflictError(f"Treadmill {device} is out of order.")
        runner = self.user_repository.get_runner_by_username(user)
        if runner is None:
            raise NotFoundError(f"Unknown runner {user}.")

        for old_run in self.run_repository.list_live_on_device_or_of_user_for_update(treadmill, runner):
            if old_run.started_at < ts:
                self._close_at_last_sample(old_run)

        run = self.run_repository.save(Run(uuid=run_uuid, user=runner, device=treadmill, type=run_type, started_at=ts))

        before_status = treadmill.status
        if treadmill.see(ts):
            treadmill.start_use()
        self.device_repository.save(treadmill, update_fields=["status", "last_seen"])

        notify_run_status(runner.id, run.id, Run.Status.LIVE)
        if treadmill.status != before_status:
            notify_devices_changed()
        return run

    @transaction.atomic
    def save_samples(self, *, samples):
        run_uuids = set()
        for sample in samples:
            run_uuids.add(sample["run_uuid"])
        runs = self.run_repository.status_by_uuid(run_uuids)

        unknown_runs = set()
        live_run_ids = {}
        for run_uuid in run_uuids:
            if run_uuid not in runs:
                unknown_runs.add(run_uuid)
            elif runs[run_uuid]["status"] == Run.Status.LIVE:
                live_run_ids[run_uuid] = runs[run_uuid]["id"]

        rows = []
        latest_by_device = {}
        for sample in samples:
            if sample["run_uuid"] not in live_run_ids:
                continue
            rows.append(
                Sample(
                    run_id=live_run_ids[sample["run_uuid"]],
                    seq=sample["seq"],
                    time=sample["ts"],
                    hr=sample["hr"],
                    speed_kmh=sample["speed_kmh"],
                    incline=sample["incline"],
                )
            )
            device = sample["device"]
            if device not in latest_by_device or sample["ts"] > latest_by_device[device]:
                latest_by_device[device] = sample["ts"]

        self.sample_repository.bulk_create(rows, ignore_conflicts=True)
        self.run_repository.touch_last_data(list(live_run_ids.values()), timezone.now())
        self.device_repository.see_many(latest_by_device)
        live_runs = set(live_run_ids.keys())
        return unknown_runs, live_runs

    @transaction.atomic
    def end_run(self, *, device, run_uuid, ts):
        run = self.run_repository.get_by_uuid_with_device_for_update(run_uuid)
        if run is None:
            raise NotFoundError(f"Unknown run {run_uuid}.")
        if run.device.serial != device:
            raise ValidationFailedError({"device": [f"Run {run_uuid} is on treadmill {run.device.serial}."]})
        if not run.is_live:
            return run
        if ts < run.started_at:
            raise ValidationFailedError({"ts": ["A run cannot end before it started."]})
        self._close(run, ts, from_device=True)
        return run

    @transaction.atomic
    def close_run(self, *, run, ts):
        self._close(run, ts, from_device=False)

    def run_watchdog(self):
        """Close stale live runs; alert on no data; mark silent treadmills offline."""
        now = timezone.now()
        result = {"ended": 0, "discarded": 0, "faults": 0, "offline": 0}
        for run in self.run_repository.list_live_with_device():
            silent_s = (now - run.last_data_at).total_seconds()
            if silent_s >= settings.STALE_RUN_MINUTES * 60:
                outcome = self.close_stale_run(run_id=run.pk)
                if outcome == STALE_ENDED:
                    result["ended"] += 1
                if outcome == STALE_DISCARDED:
                    result["discarded"] += 1
                continue
            if silent_s >= settings.NO_DATA_SECONDS:
                alert = self.alert_service.raise_alert(
                    device=run.device,
                    run=run,
                    alert_type=Alert.Type.DEVICE_FAULT,
                    message=f"{run.device.serial}: no data for over {settings.NO_DATA_SECONDS} s",
                )
                if alert is not None:
                    result["faults"] += 1
        result["offline"] = self._mark_offline_devices(now)
        return result

    def requeue_stuck_analyses(self):
        cutoff = timezone.now() - timedelta(minutes=settings.STUCK_TASK_MINUTES)
        run_ids = self.run_repository.list_ids_analyzing_ended_before(cutoff)
        for run_id in run_ids:
            tasks.analyze_run.delay(run_id)
        return len(run_ids)

    @transaction.atomic
    def close_stale_run(self, *, run_id):
        run = self.run_repository.get_by_id_for_update(run_id)
        if run is None or not run.is_live:
            return None
        return self._close_at_last_sample(run)

    @transaction.atomic
    def record_heartbeats(self, *, heartbeats):
        serials = set()
        for heartbeat in heartbeats:
            serials.add(heartbeat["device"])
        device_by_serial = {}
        for device in self.device_repository.list_by_serials_for_update(serials):
            device_by_serial[device.serial] = device

        changed_devices = {}
        status_changed = False
        for heartbeat in heartbeats:
            device = device_by_serial.get(heartbeat["device"])
            if device is None:
                continue
            if not device.see(heartbeat["ts"]):
                continue
            device.firmware = heartbeat["firmware"]
            before_status = device.status
            if device.is_offline:
                device.come_back(self.run_repository.exists_live_on_device(device))
            if device.status != before_status:
                status_changed = True
            changed_devices[device.serial] = device

        self.device_repository.bulk_update(list(changed_devices.values()), ["firmware", "status", "last_seen"])
        if status_changed:
            notify_devices_changed()

        unknown_devices = set()
        for serial in serials:
            if serial not in device_by_serial:
                unknown_devices.add(serial)
        return unknown_devices

    @transaction.atomic
    def dead_letter(self, *, routing_key, body, error, device_serial=""):
        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="replace")
        return self.dead_letter_repository.save(
            DeadLetter(
                routing_key=routing_key[:50],
                body=body,
                error=error,
                device_serial=device_serial[:40],
            )
        )

    @transaction.atomic
    def _mark_offline_devices(self, now):
        cutoff = now - timedelta(seconds=settings.DEVICE_OFFLINE_SECONDS)
        devices = self.device_repository.list_silent_since_for_update(cutoff)
        for device in devices:
            device.go_offline()
        self.device_repository.bulk_update(devices, ["status"])
        if devices:
            notify_devices_changed()
        return len(devices)

    def _close(self, run, ts, *, from_device):
        run.end(ts)
        self.run_repository.save(run, update_fields=["ended_at", "status"])

        treadmill = self.device_repository.get_by_id_for_update(run.device_id)
        before_status = treadmill.status
        is_newest_message = True
        if from_device:
            is_newest_message = treadmill.see(ts)
        if is_newest_message and not self.run_repository.exists_live_on_device(treadmill):
            treadmill.finish_use()
        self.device_repository.save(treadmill, update_fields=["status", "last_seen"])

        notify_run_status(run.user_id, run.pk, Run.Status.ANALYZING)
        if treadmill.status != before_status:
            notify_devices_changed()

        run_id = run.pk
        transaction.on_commit(lambda: tasks.analyze_run.delay(run_id))

    def _close_at_last_sample(self, run):
        last_time = self.sample_repository.last_time_of_run(run)
        if last_time is None:
            self._discard(run)
            return STALE_DISCARDED
        self._close(run, max(last_time, run.started_at), from_device=False)
        return STALE_ENDED

    def _discard(self, run):
        treadmill = self.device_repository.get_by_id_for_update(run.device_id)
        before_status = treadmill.status
        notify_run_status(run.user_id, run.pk, RUN_DISCARDED)
        self.run_repository.delete(run)
        if not self.run_repository.exists_live_on_device(treadmill):
            treadmill.finish_use()
            self.device_repository.save(treadmill, update_fields=["status"])
        if treadmill.status != before_status:
            notify_devices_changed()
