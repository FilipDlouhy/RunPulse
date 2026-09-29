from .alerts import AlertRepository
from .devices import DeviceRepository

device_repository = DeviceRepository()
alert_repository = AlertRepository()

__all__ = ["alert_repository", "device_repository"]
