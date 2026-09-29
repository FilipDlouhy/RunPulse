from apps.gym_admin.repositories import alert_repository, device_repository
from apps.runners.repositories import runner_profile_repository
from apps.runs.repositories import run_repository, usage_hourly_repository
from apps.user.repositories import user_repository

from .alerts import AlertService
from .devices import DeviceService
from .seed import SeedService
from .stats import GymStatsService

device_service = DeviceService(device_repository=device_repository)
alert_service = AlertService(alert_repository=alert_repository)
gym_stats_service = GymStatsService(
    device_repository=device_repository,
    run_repository=run_repository,
    usage_hourly_repository=usage_hourly_repository,
    alert_service=alert_service,
)
seed_service = SeedService(
    user_repository=user_repository,
    runner_profile_repository=runner_profile_repository,
    device_repository=device_repository,
)

__all__ = ["alert_service", "device_service", "gym_stats_service", "seed_service"]
