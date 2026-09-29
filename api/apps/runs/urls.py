from rest_framework.routers import SimpleRouter

from .controllers.records import RecordController, WeeklyStatsController
from .controllers.runs import RunController

router = SimpleRouter()
router.register("runs", RunController, basename="run")
router.register("records", RecordController, basename="records")
router.register("stats", WeeklyStatsController, basename="stats")

urlpatterns = router.urls
