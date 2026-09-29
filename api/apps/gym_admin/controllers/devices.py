from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.gym_admin.dtos import DeviceResponseSerializer
from apps.gym_admin.services import device_service
from apps.runs.services import run_service
from common.permissions import IsGymAdmin


class DeviceController(ViewSet):
    permission_classes = [IsGymAdmin]
    lookup_value_regex = r"\d+"

    @action(detail=True, methods=["post"], url_path="out-of-order")
    def out_of_order(self, request, pk):
        device = device_service.mark_out_of_order(device_id=pk)
        run_service.stop_runs_on_device(device=device)
        return Response(DeviceResponseSerializer(device).data)

    @action(detail=True, methods=["post"], url_path="service-done")
    def service_done(self, request, pk):
        device = device_service.mark_service_done(device_id=pk)
        return Response(DeviceResponseSerializer(device).data)
