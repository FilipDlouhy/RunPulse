from rest_framework.routers import SimpleRouter

from .controllers.tech import DeadLetterController, TechController

router = SimpleRouter()
router.register("tech", TechController, basename="tech")
router.register("dlq", DeadLetterController, basename="dead-letter")

urlpatterns = router.urls
