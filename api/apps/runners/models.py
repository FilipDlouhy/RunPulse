from django.conf import settings
from django.db import models

GOAL_TIME_MIN_S = 600         # minimum goal time: 10 minutes
GOAL_TIME_MAX_S = 86400       # maximum goal time: 24 hours


class RaceDistance(models.IntegerChoices):
    K5 = 5000, "5 km"
    K10 = 10000, "10 km"
    HALF = 21097, "Half marathon"


class RunnerProfile(models.Model):
    """Runner's personal fitness data: age, weight, heart rate zones, goal race."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    weight_kg = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    hr_rest = models.PositiveSmallIntegerField(null=True, blank=True)
    hr_max = models.PositiveSmallIntegerField(null=True, blank=True)
    goal_distance = models.PositiveIntegerField(choices=RaceDistance.choices, null=True, blank=True)
    goal_time_s = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user}"
