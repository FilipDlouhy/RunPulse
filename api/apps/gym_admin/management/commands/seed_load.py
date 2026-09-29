from django.core.management.base import BaseCommand

from apps.gym_admin.services import seed_service
from apps.gym_admin.services.seed import LOAD_TREADMILLS


class Command(BaseCommand):
    help = "Create the loadbot user and the treadmills for the load test. Safe to run repeatedly."

    def handle(self, *args, **options):
        user = seed_service.seed_load()
        self.stdout.write(self.style.SUCCESS(f"Seeded user {user.username} and {LOAD_TREADMILLS} load test treadmills."))
