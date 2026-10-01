from django.db.models import Avg, F, Max, Sum
from django.db.models.functions import Floor

from apps.runs.models import Sample
from common.repositories import BaseRepository


class SampleRepository(BaseRepository[Sample]):
    """Fetch and aggregate telemetry samples: distance, heart rate, bucketing."""
    model = Sample

    def get_last_of_run(self, run):
        return self.model.objects.filter(run=run).order_by("-seq").first()

    def last_time_of_run(self, run):
        return self.model.objects.filter(run=run).aggregate(last=Max("time"))["last"]

    def distance_m_of_run(self, run):
        total = self.model.objects.filter(run=run).aggregate(total=Sum("speed_kmh"))["total"]
        if total is None:
            return 0.0
        return total / 3.6

    def distance_m_before(self, run, seq):
        total = self.model.objects.filter(run=run, seq__lt=seq).aggregate(total=Sum("speed_kmh"))["total"]
        if total is None:
            return 0.0
        return total / 3.6

    def list_of_run_since(self, run, since):
        return list(self.model.objects.filter(run=run, time__gte=since).order_by("seq"))

    def rows_of_run(self, run):
        return list(self.model.objects.filter(run=run).order_by("seq").values_list("seq", "hr", "speed_kmh", "incline"))

    def bucketed_of_run(self, run, step):
        return list(
            self.model.objects.filter(run=run)
            .annotate(bucket=Floor(F("seq") / step))
            .values("bucket")
            .annotate(hr=Avg("hr"), speed_kmh=Avg("speed_kmh"), incline=Avg("incline"))
            .order_by("bucket")
        )

