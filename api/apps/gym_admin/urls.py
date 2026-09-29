from rest_framework.routers import SimpleRouter

from .controllers.alerts import AlertController
from .controllers.devices import DeviceController
from .controllers.gym import GymController

router = SimpleRouter()
router.register("gym", GymController, basename="gym")
router.register("devices", DeviceController, basename="device")
router.register("alerts", AlertController, basename="alert")

urlpatterns = router.urls
