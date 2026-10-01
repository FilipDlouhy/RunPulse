"""
Demo data (users, runner profiles, 30 treadmills) and extra treadmills for the load test.
"""
import random
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from faker import Faker

from apps.gym_admin.dtos import DemoSeed
from apps.gym_admin.models import Device
from apps.runners.models import RaceDistance
from apps.user.models import User

DEMO_PASSWORD = "demo1234"
ADMIN_PASSWORD = "admin"
FILIP_PASSWORD = "filip123"
SEED = 42

TREADMILL_COUNT = 30
OVERDUE_TREADMILLS = {"TREAD-03", "TREAD-07"}
FAULTY_TREADMILL = "TREAD-10"
TREADMILL_HOURS = [120, 260, 540, 75, 310, 190, 515, 405, 45, 330, 220, 150]

MEMBER_COUNT = 120

LOAD_USERNAME = "loadbot"
LOAD_EMAIL = "loadbot@demo.cz"
LOAD_TREADMILLS = 500


def member_traits(index):
    rng = random.Random(SEED + index)
    age = rng.randint(20, 55)
    hr_rest = rng.randint(48, 68)
    hr_max = 208 - round(0.7 * age)
    return age, hr_rest, hr_max


class SeedService:
    """Generates demo users, runner profiles, and treadmill devices with realistic data."""

    def __init__(self, *, user_repository, runner_profile_repository, device_repository):
        self.user_repository = user_repository
        self.runner_profile_repository = runner_profile_repository
        self.device_repository = device_repository

    def is_seeded(self):
        return self.user_repository.exists_by_username("manager")

    @transaction.atomic
    def seed_demo(self):
        manager = self._user(username="manager", email="manager@demo.cz", role=User.Role.GYM_ADMIN)
        runner = self._user(username="runner", email="runner@demo.cz", role=User.Role.RUNNER)
        self._user(
            username="admin",
            email="admin@demo.cz",
            role=User.Role.GYM_ADMIN,
            password=ADMIN_PASSWORD,
            superuser=True,
        )
        self._user(username="filip", email="filip@demo.cz", role=User.Role.RUNNER, password=FILIP_PASSWORD)
        self.runner_profile_repository.update_or_create_for_user(
            runner,
            {
                "weight_kg": Decimal("72.5"),
                "birth_date": date(1994, 5, 14),
                "hr_rest": 52,
                "hr_max": 188,
                "goal_distance": RaceDistance.K10,
                "goal_time_s": 50 * 60,
            },
        )

        members = []
        for index in range(1, MEMBER_COUNT + 1):
            members.append(self._member(index))

        devices = self._treadmills()
        return DemoSeed(manager=manager, runner=runner, member_count=len(members), device_count=len(devices))

    @transaction.atomic
    def seed_load(self):
        user = self._user(username=LOAD_USERNAME, email=LOAD_EMAIL, role=User.Role.RUNNER)
        devices = []
        for i in range(1, LOAD_TREADMILLS + 1):
            devices.append(Device(serial=f"LOAD-{i:03}", status=Device.Status.FREE))
        self.device_repository.bulk_create(devices, ignore_conflicts=True)
        return user

    def _user(
        self,
        *,
        username,
        email,
        role,
        password=DEMO_PASSWORD,
        superuser=False,
        first_name=None,
        last_name=None,
    ):
        user = self.user_repository.get_or_create_by_username(username)
        user.email = email
        user.role = role
        if superuser:
            user.is_staff = True
            user.is_superuser = True
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        user.set_password(password)
        return self.user_repository.save(user, validate=False)

    def _member(self, index):
        age, hr_rest, hr_max = member_traits(index)
        username = f"member{index:03d}"
        fake = Faker("en_US")
        fake.seed_instance(SEED + index)
        user = self._user(
            username=username,
            email=f"{username}@demo.cz",
            role=User.Role.RUNNER,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
        )
        self.runner_profile_repository.update_or_create_for_user(
            user,
            {
                "birth_date": date(timezone.localdate().year - age, 6, 1),
                "hr_rest": hr_rest,
                "hr_max": hr_max,
            },
        )
        return user

    def _treadmills(self):
        now = timezone.now()
        devices = []
        for i in range(1, TREADMILL_COUNT + 1):
            serial = f"TREAD-{i:02}"
            hours = TREADMILL_HOURS[(i - 1) % len(TREADMILL_HOURS)]

            if serial in OVERDUE_TREADMILLS:
                since_service = hours
            else:
                since_service = hours % 400

            if serial == FAULTY_TREADMILL:
                status = Device.Status.OUT_OF_ORDER
            else:
                status = Device.Status.FREE

            device = self.device_repository.update_or_create_by_serial(
                serial,
                {
                    "status": status,
                    "firmware": "3.2.1",
                    "last_seen": now,
                    "total_hours": Decimal(hours + 800),
                    "hours_since_service": Decimal(since_service),
                    "needs_service": since_service >= settings.SERVICE_INTERVAL_HOURS,
                },
            )
            devices.append(device)
        return devices
