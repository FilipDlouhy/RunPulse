from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.gym_admin.dtos import AlertResponseSerializer
from apps.gym_admin.services import alert_service
from common.permissions import IsGymAdmin


class AlertController(ViewSet):
    permission_classes = [IsGymAdmin]
    lookup_value_regex = r"\d+"

    @action(detail=True, methods=["post"])
    def ack(self, request, pk):
        alert = alert_service.acknowledge(alert_id=pk)
        return Response(AlertResponseSerializer(alert).data)
