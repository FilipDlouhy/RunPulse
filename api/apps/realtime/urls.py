from rest_framework.routers import SimpleRouter

from .controllers.health import HealthController

router = SimpleRouter()
router.register("health", HealthController, basename="health")

urlpatterns = router.urls
