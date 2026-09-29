from rest_framework.routers import SimpleRouter

from .controllers.profiles import RunnerProfileController

router = SimpleRouter()
router.register("", RunnerProfileController, basename="runner")

urlpatterns = router.urls
