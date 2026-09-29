from django.db import transaction

from apps.gym_admin.models import Alert
from apps.realtime.notify import notify_alert
from common.exceptions import NotFoundError

ALERT_HISTORY = 50


class AlertService:
    def __init__(self, *, alert_repository):
        self.alert_repository = alert_repository

    @transaction.atomic
    def raise_alert(self, *, device, alert_type, message, run=None):
        if self.alert_repository.get_open(device, run, alert_type) is not None:
            return None
        alert = Alert(device=device, run=run, type=alert_type, message=message[:300])
        self.alert_repository.save(alert)
        notify_alert(alert)
        return alert

    def open_alerts(self):
        return self.alert_repository.list_open_with_device(ALERT_HISTORY)

    def open_for_run(self, *, run):
        return self.alert_repository.list_open_of_run(run)

    @transaction.atomic
    def acknowledge(self, *, alert_id):
        alert = self.alert_repository.get_with_device_for_update(alert_id)
        if alert is None:
            raise NotFoundError("Alert not found.")
        alert.acknowledge()
        self.alert_repository.save(alert, update_fields=["acknowledged_at"])
        return alert
