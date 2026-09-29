from dataclasses import dataclass
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from rest_framework import serializers

from .calculations import age
from .models import GOAL_TIME_MAX_S, GOAL_TIME_MIN_S, RaceDistance, RunnerProfile

MIN_AGE = 10
MAX_AGE = 100


@dataclass(frozen=True)
class RunnerProfileOverview:
    profile: RunnerProfile
    age: int | None
    hr_max_effective: int | None
    hr_max_estimated: bool
    zones: list
    goal: dict | None


def _range(low, high):
    return [MinValueValidator(low), MaxValueValidator(high)]


class UpdateRunnerProfileRequestSerializer(serializers.Serializer):
    weight_kg = serializers.DecimalField(
        max_digits=4,
        decimal_places=1,
        allow_null=True,
        required=False,
        validators=_range(Decimal(30), Decimal(250)),
    )
    birth_date = serializers.DateField(allow_null=True, required=False)
    hr_rest = serializers.IntegerField(allow_null=True, required=False, validators=_range(30, 100))
    hr_max = serializers.IntegerField(allow_null=True, required=False, validators=_range(120, 230))
    goal_distance = serializers.ChoiceField(choices=RaceDistance.choices, allow_null=True, required=False)
    goal_time_s = serializers.IntegerField(
        allow_null=True,
        required=False,
        validators=_range(GOAL_TIME_MIN_S, GOAL_TIME_MAX_S),
    )

    def validate_birth_date(self, birth_date):
        if birth_date is None:
            return birth_date
        runner_age = age(birth_date, timezone.localdate())
        if runner_age < MIN_AGE or runner_age > MAX_AGE:
            raise serializers.ValidationError(f"Age must be between {MIN_AGE} and {MAX_AGE} years.")
        return birth_date


class HeartRateZoneResponseSerializer(serializers.Serializer):
    zone = serializers.IntegerField()
    min_bpm = serializers.IntegerField()
    max_bpm = serializers.IntegerField()


class RacePredictionResponseSerializer(serializers.Serializer):
    distance = serializers.IntegerField()
    label = serializers.CharField()
    time_s = serializers.IntegerField()


class GoalResponseSerializer(serializers.Serializer):
    pace_s_per_km = serializers.IntegerField()
    predictions = RacePredictionResponseSerializer(many=True)


class RunnerProfileResponseSerializer(serializers.Serializer):
    weight_kg = serializers.DecimalField(max_digits=4, decimal_places=1, source="profile.weight_kg")
    birth_date = serializers.DateField(source="profile.birth_date")
    hr_rest = serializers.IntegerField(source="profile.hr_rest")
    hr_max = serializers.IntegerField(source="profile.hr_max")
    goal_distance = serializers.IntegerField(source="profile.goal_distance")
    goal_time_s = serializers.IntegerField(source="profile.goal_time_s")
    age = serializers.IntegerField()
    hr_max_effective = serializers.IntegerField()
    hr_max_estimated = serializers.BooleanField()
    zones = HeartRateZoneResponseSerializer(many=True)
    goal = GoalResponseSerializer(allow_null=True)
