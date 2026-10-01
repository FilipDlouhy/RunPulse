from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.runs.dtos import PersonalRecordResponseSerializer, WeeklyStatResponseSerializer, WeeklyStatsRequestSerializer
from apps.runs.services import record_service
from common.permissions import IsRunner


class RecordController(ViewSet):
    """List personal records (best times for 1K, 5K, 10K)."""
    permission_classes = [IsRunner]

    def list(self, request):
        records = record_service.best_records(user=request.user)
        return Response(PersonalRecordResponseSerializer(records, many=True).data)


class WeeklyStatsController(ViewSet):
    """Weekly aggregates: runs count, distance, duration, training impulse."""
    permission_classes = [IsRunner]

    @action(detail=False, methods=["get"])
    def weekly(self, request):
        serializer = WeeklyStatsRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        stats = record_service.weekly_stats(user=request.user, weeks=serializer.validated_data["weeks"])
        return Response(WeeklyStatResponseSerializer(stats, many=True).data)
