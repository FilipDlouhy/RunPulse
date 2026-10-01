from django.db import transaction

from apps.realtime.notify import notify_devices_changed
from apps.runs.messaging import send_device_status
from common.exceptions import ConflictError, NotFoundError


class DeviceService:
    """Treadmill actions of the gym admin."""

    def __init__(self, *, device_repository):
        self.device_repository = device_repository

    def list_devices(self):
        return self.device_repository.get_all()

    @transaction.atomic
    def mark_out_of_order(self, *, device_id):
        """Take the treadmill out of service, the simulator stops using it."""
        device = self._device_for_update(device_id)
        if device.is_out_of_order:
            raise ConflictError("The treadmill is already out of order.")
        device.mark_out_of_order()
        self.device_repository.save(device, update_fields=["status"])
        notify_devices_changed()
        self._send_status_on_commit(device)
        return device

    @transaction.atomic
    def mark_service_done(self, *, device_id):
        device = self._device_for_update(device_id)
        device.mark_service_done()
        self.device_repository.save(device, update_fields=["hours_since_service", "needs_service", "status"])
        notify_devices_changed()
        self._send_status_on_commit(device)
        return device

    def _send_status_on_commit(self, device):
        # after commit only, a RabbitMQ outage must not fail the admin action
        transaction.on_commit(lambda: send_device_status(device.serial, device.status), robust=True)

    def _device_for_update(self, device_id):
        device = self.device_repository.get_by_id_for_update(device_id)
        if device is None:
            raise NotFoundError("Treadmill not found.")
        return device
