from django.db import connections
from django.db.models import Q
from django.utils import timezone

from apps.gym_admin.models import Device
from common.repositories import BaseRepository


class DeviceRepository(BaseRepository[Device]):
    """Data access for treadmill devices."""

    model = Device

    def get_by_serial(self, serial):
        return self.model.objects.filter(serial=serial).first()

    def get_by_serial_for_update(self, serial):
        return self.model.objects.select_for_update().filter(serial=serial).first()

    def list_by_serials_for_update(self, serials):
        return list(self.model.objects.select_for_update().filter(serial__in=serials).order_by("pk"))

    def list_silent_since_for_update(self, cutoff):
        """Get in-use devices that haven't reported status since cutoff."""
        return list(
            self.model.objects.select_for_update()
            .exclude(status=Device.Status.OFFLINE)
            .exclude(status=Device.Status.OUT_OF_ORDER)
            .filter(Q(last_seen__isnull=True) | Q(last_seen__lt=cutoff))
        )

    def update_or_create_by_serial(self, serial, fields):
        """Upsert device by serial, return the device."""
        device, _created = self.model.objects.update_or_create(serial=serial, defaults=fields)
        return device

    def see_many(self, last_seen_by_serial):
        """Bulk update last_seen timestamps using raw SQL for performance."""
        if not last_seen_by_serial:
            return
        now = timezone.now()
        serials = []
        times = []
        for serial, ts in last_seen_by_serial.items():
            serials.append(serial)
            times.append(min(ts, now))
        with connections[self.model.objects.db].cursor() as cursor:
            cursor.execute(
                f"UPDATE {self.model._meta.db_table} AS device SET last_seen = seen.ts "
                "FROM unnest(%s::text[], %s::timestamptz[]) AS seen(serial, ts) "
                "WHERE device.serial = seen.serial AND (device.last_seen IS NULL OR device.last_seen < seen.ts)",
                [serials, times],
            )
