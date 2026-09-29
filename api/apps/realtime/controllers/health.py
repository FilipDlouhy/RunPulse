from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.realtime.services import health_service


class HealthController(ViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]

    def list(self, request):
        result = health_service.check()
        if result["status"] == "ok":
            return Response(result, status=200)
        return Response(result, status=503)
