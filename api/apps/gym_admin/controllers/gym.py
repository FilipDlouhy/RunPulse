from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.gym_admin.dtos import (
    DeviceResponseSerializer,
    GymOverviewResponseSerializer,
    HeatmapRequestSerializer,
    HeatmapResponseSerializer,
)
from apps.gym_admin.services import device_service, gym_stats_service
from common.permissions import IsGymAdmin


class GymController(ViewSet):
    """API endpoints for gym overview, device status, and usage analytics."""

    permission_classes = [IsGymAdmin]

    @action(detail=False, methods=["get"])
    def overview(self, request):
        overview = gym_stats_service.overview()
        return Response(GymOverviewResponseSerializer(overview).data)

    @action(detail=False, methods=["get"])
    def devices(self, request):
        devices = device_service.list_devices()
        return Response(DeviceResponseSerializer(devices, many=True).data)

    @action(detail=False, methods=["get"], url_path="usage/heatmap")
    def usage_heatmap(self, request):
        serializer = HeatmapRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        heatmap = gym_stats_service.heatmap(weeks=serializer.validated_data["weeks"])
        return Response(HeatmapResponseSerializer(heatmap).data)
