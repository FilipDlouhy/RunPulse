from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncWeek
from django.utils import timezone

from apps.runs.models import Run
from common.repositories import BaseRepository


class RunRepository(BaseRepository[Run]):
    """Queries for live, finished, and analyzing runs; live runs per device/user."""
    model = Run

    def get_by_uuid(self, run_uuid):
        return self.model.objects.filter(uuid=run_uuid).first()

    def get_by_uuid_with_device_for_update(self, run_uuid):
        return self.model.objects.select_for_update().select_related("device").filter(uuid=run_uuid).first()

    def get_live_by_uuid_with_device(self, run_uuid):
        return self.model.objects.filter(status=Run.Status.LIVE).select_related("device").filter(uuid=run_uuid).first()

    def get_analyzing_by_id(self, run_id):
        return self.model.objects.filter(status=Run.Status.ANALYZING, pk=run_id).first()

    def list_ids_analyzing_ended_before(self, cutoff):
        return list(
            self.model.objects.filter(status=Run.Status.ANALYZING, ended_at__lt=cutoff).values_list("pk", flat=True)
        )

    def get_with_device_and_user(self, run_id):
        return self.model.objects.select_related("device", "user").filter(pk=run_id).first()

    def get_of_user(self, user, run_id):
        return self.model.objects.filter(user=user, pk=run_id).first()

    def get_of_user_with_summary(self, user, run_id):
        return self.model.objects.select_related("summary", "device").filter(user=user, pk=run_id).first()

    def get_of_user_for_update(self, user, run_id):
        return self.model.objects.select_for_update().filter(user=user, pk=run_id).first()

    def get_of_user_with_device_for_update(self, user, run_id):
        return self.model.objects.select_for_update().select_related("device").filter(user=user, pk=run_id).first()

    def get_current_live_with_summary(self, user):
        return (
            self.model.objects.select_related("summary", "device")
            .filter(status=Run.Status.LIVE, user=user)
            .order_by("-started_at")
            .first()
        )

    def status_by_uuid(self, run_uuids):
        rows = self.model.objects.filter(uuid__in=run_uuids).values("uuid", "id", "status")
        result = {}
        for row in rows:
            result[row["uuid"]] = row
        return result

    def touch_last_data(self, run_ids, ts):
        self.model.objects.filter(pk__in=run_ids).update(last_data_at=ts)

    def list_live_with_device(self):
        return list(self.model.objects.filter(status=Run.Status.LIVE).select_related("device"))

    def list_finished_of_user_with_summary(self, user, run_types=None):
        runs = self.model.objects.filter(user=user).exclude(status=Run.Status.LIVE).select_related("summary", "device")
        if run_types is not None:
            runs = runs.filter(type__in=run_types)
        return list(runs)

    def exists_live_on_device(self, device):
        return self.model.objects.filter(status=Run.Status.LIVE, device=device).exists()

    def list_live_on_device_for_update(self, device):
        return list(self.model.objects.select_for_update().filter(status=Run.Status.LIVE, device=device))

    def list_live_on_device_or_of_user_for_update(self, device, user):
        runs = self.model.objects.select_for_update().filter(status=Run.Status.LIVE)
        return list(runs.filter(Q(device=device) | Q(user=user)))

    def count_started_since(self, since):
        return self.model.objects.filter(started_at__gte=since).count()

    def weekly_totals_of_user_since(self, user, since):
        return list(
            self.model.objects.filter(user=user, status=Run.Status.DONE, started_at__gte=since)
            .annotate(week=TruncWeek("started_at", tzinfo=timezone.get_current_timezone()))
            .values("week")
            .annotate(
                runs=Count("id"),
                distance_m=Sum("summary__distance_m"),
                duration_s=Sum("summary__duration_s"),
                trimp=Sum("summary__trimp"),
            )
            .order_by("week")
        )
