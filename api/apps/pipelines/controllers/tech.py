from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.pipelines.dtos import TechOverviewResponseSerializer
from apps.pipelines.services import tech_service
from common.permissions import IsGymAdmin


class TechController(ViewSet):
    permission_classes = [IsGymAdmin]

    def list(self, request):
        overview = tech_service.overview()
        return Response(TechOverviewResponseSerializer(overview).data)


class DeadLetterController(ViewSet):
    permission_classes = [IsGymAdmin]
    lookup_value_regex = r"\d+"

    @action(detail=True, methods=["post"])
    def retry(self, request, pk):
        tech_service.retry_dead_letter(dead_letter_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
