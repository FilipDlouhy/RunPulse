from apps.runners.repositories import runner_profile_repository

from .profiles import RunnerProfileService

runner_profile_service = RunnerProfileService(runner_profile_repository=runner_profile_repository)

__all__ = ["runner_profile_service"]
