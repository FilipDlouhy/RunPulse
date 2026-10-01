from django.db import transaction
from django.utils import timezone

from apps.runners.calculations import age, effective_hr_max, goal_summary, karvonen_zones
from apps.runners.dtos import RunnerProfileOverview
from apps.runners.models import RunnerProfile
from common.exceptions import ValidationFailedError


class RunnerProfileService:
    """Runner profile management: fitness data, zones, race predictions."""

    def __init__(self, *, runner_profile_repository):
        self.runner_profile_repository = runner_profile_repository

    @transaction.atomic
    def get_overview(self, *, user):
        profile = self._find_or_create(user)
        return self._overview(profile)

    @transaction.atomic
    def update_profile(self, *, user, changes):
        profile = self._find_or_create(user)
        self._validate(profile, changes)
        if "weight_kg" in changes:
            profile.weight_kg = changes["weight_kg"]
        if "birth_date" in changes:
            profile.birth_date = changes["birth_date"]
        if "hr_rest" in changes:
            profile.hr_rest = changes["hr_rest"]
        if "hr_max" in changes:
            profile.hr_max = changes["hr_max"]
        if "goal_distance" in changes:
            profile.goal_distance = changes["goal_distance"]
        if "goal_time_s" in changes:
            profile.goal_time_s = changes["goal_time_s"]
        self.runner_profile_repository.save(profile)
        return self._overview(profile)

    def _find_or_create(self, user):
        profile = self.runner_profile_repository.get_by_user(user)
        if profile is None:
            profile = self.runner_profile_repository.save(RunnerProfile(user=user))
        return profile

    def _validate(self, profile, changes):
        goal_distance = changes.get("goal_distance", profile.goal_distance)
        goal_time_s = changes.get("goal_time_s", profile.goal_time_s)
        has_distance = goal_distance is not None
        has_time = goal_time_s is not None
        if has_distance != has_time:
            raise ValidationFailedError({"goal_time_s": ["Enter the goal distance and the goal time together."]})

    def _overview(self, profile):
        today = timezone.localdate()
        hr_max, estimated = effective_hr_max(profile, today)

        runner_age = None
        if profile.birth_date:
            runner_age = age(profile.birth_date, today)

        zones = []
        if profile.hr_rest and hr_max:
            zones = karvonen_zones(profile.hr_rest, hr_max)

        return RunnerProfileOverview(
            profile=profile,
            age=runner_age,
            hr_max_effective=hr_max,
            hr_max_estimated=estimated,
            zones=zones,
            goal=goal_summary(profile),
        )
