from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.runners.dtos import RunnerProfileResponseSerializer, UpdateRunnerProfileRequestSerializer
from apps.runners.services import runner_profile_service
from common.permissions import IsRunner


class RunnerProfileController(ViewSet):
    permission_classes = [IsRunner]

    @action(detail=False, methods=["get"])
    def profile(self, request):
        overview = runner_profile_service.get_overview(user=request.user)
        return Response(RunnerProfileResponseSerializer(overview).data)

    @profile.mapping.put
    def update_profile(self, request):
        serializer = UpdateRunnerProfileRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        overview = runner_profile_service.update_profile(user=request.user, changes=serializer.validated_data)
        return Response(RunnerProfileResponseSerializer(overview).data)
