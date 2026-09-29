from apps.gym_admin.repositories import device_repository
from apps.gym_admin.services import alert_service
from apps.runners.repositories import runner_profile_repository
from apps.runs.repositories import (
    dead_letter_repository,
    personal_record_repository,
    run_repository,
    sample_repository,
)
from apps.user.repositories import user_repository

from .alarms import AlarmMonitor
from .records import RecordService
from .runs import RunService
from .telemetry import TelemetryService

telemetry_service = TelemetryService(
    run_repository=run_repository,
    sample_repository=sample_repository,
    dead_letter_repository=dead_letter_repository,
    device_repository=device_repository,
    user_repository=user_repository,
    alert_service=alert_service,
)
record_service = RecordService(
    personal_record_repository=personal_record_repository,
    run_repository=run_repository,
)
run_service = RunService(
    run_repository=run_repository,
    sample_repository=sample_repository,
    runner_profile_repository=runner_profile_repository,
    telemetry_service=telemetry_service,
    alert_service=alert_service,
    record_service=record_service,
)
alarm_monitor = AlarmMonitor(
    run_repository=run_repository,
    sample_repository=sample_repository,
    device_repository=device_repository,
    runner_profile_repository=runner_profile_repository,
    alert_service=alert_service,
)

__all__ = ["alarm_monitor", "record_service", "run_service", "telemetry_service"]
