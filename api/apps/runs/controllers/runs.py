from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.runs.dtos import (
    ListRunsRequestSerializer,
    ListSamplesRequestSerializer,
    LiveRunResponseSerializer,
    RunDetailResponseSerializer,
    RunListItemResponseSerializer,
    SamplePointResponseSerializer,
    UpdateRunRequestSerializer,
)
from apps.runs.services import run_service
from common.permissions import IsRunner


class RunController(ViewSet):
    permission_classes = [IsRunner]
    lookup_value_regex = r"\d+"

    def list(self, request):
        filters = ListRunsRequestSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        runs = run_service.list_runs(user=request.user, run_type=filters.validated_data.get("run_type"))
        return Response(RunListItemResponseSerializer(runs, many=True).data)

    def retrieve(self, request, pk):
        run = run_service.get_run(user=request.user, run_id=pk)
        return Response(RunDetailResponseSerializer(run).data)

    def partial_update(self, request, pk):
        serializer = UpdateRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = run_service.update_run(user=request.user, run_id=pk, rpe=serializer.validated_data["rpe"])
        return Response(RunDetailResponseSerializer(run).data)

    @action(detail=True, methods=["get"])
    def samples(self, request, pk):
        serializer = ListSamplesRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        samples = run_service.list_samples(user=request.user, run_id=pk, step=serializer.validated_data["step"])
        return Response(SamplePointResponseSerializer(samples, many=True).data)

    @action(detail=True, methods=["post"])
    def stop(self, request, pk):
        run = run_service.stop_run(user=request.user, run_id=pk)
        return Response(RunDetailResponseSerializer(run).data)

    @action(detail=False, methods=["get"], url_path="live")
    def current_live(self, request):
        state = run_service.current_live_run(user=request.user)
        if state is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(LiveRunResponseSerializer(state).data)
