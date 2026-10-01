from apps.gym_admin.models import Alert
from common.repositories import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    """Data access for device and run alerts."""

    model = Alert

    def get_open(self, device, run, alert_type):
        return self.model.objects.filter(acknowledged_at__isnull=True, device=device, run=run, type=alert_type).first()

    def get_with_device_for_update(self, alert_id):
        return self.model.objects.select_for_update(of=("self",)).select_related("device").filter(pk=alert_id).first()

    def list_open_with_device(self, limit):
        return list(self.model.objects.select_related("device").filter(acknowledged_at__isnull=True)[:limit])

    def list_open_of_run(self, run):
        return list(self.model.objects.filter(run=run, acknowledged_at__isnull=True))
