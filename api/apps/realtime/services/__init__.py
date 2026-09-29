from apps.realtime.repositories import health_repository

from .health import HealthService

health_service = HealthService(health_repository=health_repository)

__all__ = ["health_service"]
