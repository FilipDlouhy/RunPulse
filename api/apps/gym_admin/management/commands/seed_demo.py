from django.conf import settings
from django.core.management.base import BaseCommand

from apps.gym_admin.services import seed_service


class Command(BaseCommand):
    help = "Create the demo gym's treadmills and users. Safe to run repeatedly."

    def add_arguments(self, parser):
        parser.add_argument("--if-empty", action="store_true", help="Skip when the demo data already exist.")

    def handle(self, *args, **options):
        if options["if_empty"] and seed_service.is_seeded():
            self.stdout.write("Demo data already exist, skipping.")
            return
        seeded = seed_service.seed_demo()
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {settings.GYM_NAME} with {seeded.device_count} treadmills, users {seeded.manager.username} "
            f"and {seeded.runner.username} and {seeded.member_count} members."
        ))
