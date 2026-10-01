from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """User account with role-based access: runner or gym admin."""

    class Role(models.TextChoices):
        RUNNER = "RUNNER", "Runner"
        GYM_ADMIN = "GYM_ADMIN", "Gym admin"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.RUNNER)

    objects = UserManager()

    @property
    def is_runner(self):
        return self.role == self.Role.RUNNER

    @property
    def is_gym_admin(self):
        return self.role == self.Role.GYM_ADMIN
