import pika
import redis
from django.conf import settings


class HealthService:
    """Check availability of database, RabbitMQ, and Redis."""
    def __init__(self, *, health_repository):
        self.health_repository = health_repository

    def check(self):
        """Return status and per-service health checks."""
        checks = {"db": self._db(), "rabbitmq": self._rabbitmq(), "redis": self._redis()}
        if all(checks.values()):
            status = "ok"
        else:
            status = "error"
        return {"status": status, "checks": checks}

    def _db(self):
        """Ping database; return True if available."""
        try:
            self.health_repository.ping()
            return True
        except Exception:
            return False

    def _rabbitmq(self):
        """Connect to RabbitMQ; return True if reachable."""
        try:
            params = pika.URLParameters(settings.RABBITMQ_URL)
            params.socket_timeout = 2
            params.blocked_connection_timeout = 2
            connection = pika.BlockingConnection(params)
            connection.close()
            return True
        except Exception:
            return False

    def _redis(self):
        """Ping Redis; return True if available."""
        try:
            client = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2)
            return bool(client.ping())
        except Exception:
            return False
