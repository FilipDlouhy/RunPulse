from django.db.models import Avg, Count, F, Max, Q

from apps.pipelines.models import PipelineRun, PipelineStatus, PipelineStep
from common.repositories import BaseRepository


class PipelineRunRepository(BaseRepository[PipelineRun]):
    model = PipelineRun

    def stats_since(self, since):
        return self.model.objects.filter(started_at__gte=since).aggregate(
            total=Count("id"),
            failed=Count("id", filter=Q(status=PipelineStatus.FAILED)),
            avg_duration=Avg(F("finished_at") - F("started_at"), filter=Q(finished_at__isnull=False)),
        )

    def list_recent_with_steps_since(self, since, limit):
        return list(
            self.model.objects.filter(started_at__gte=since)
            .select_related("run__device")
            .prefetch_related("steps")[:limit]
        )


class PipelineStepRepository(BaseRepository[PipelineStep]):
    model = PipelineStep

    def slowest_since(self, since, limit):
        return list(
            self.model.objects.filter(pipeline_run__in=PipelineRun.objects.filter(started_at__gte=since))
            .filter(duration_ms__isnull=False)
            .values("name")
            .annotate(avg_ms=Avg("duration_ms"), max_ms=Max("duration_ms"), count=Count("id"))
            .order_by("-avg_ms")[:limit]
        )
