from django.conf import settings
from django.db import models
from django.utils import timezone


class Device(models.Model):
    """Treadmill device in the gym, tracks status, usage, and maintenance."""

    class Status(models.TextChoices):
        FREE = "FREE", "Free"
        IN_USE = "IN_USE", "In use"
        OFFLINE = "OFFLINE", "Offline"
        OUT_OF_ORDER = "OUT_OF_ORDER", "Out of order"

    serial = models.CharField(max_length=40, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OFFLINE)
    firmware = models.CharField(max_length=40, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    hours_since_service = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    needs_service = models.BooleanField(default=False)

    class Meta:
        ordering = ["serial"]

    def __str__(self):
        return self.serial

    @property
    def is_out_of_order(self):
        return self.status == self.Status.OUT_OF_ORDER

    @property
    def is_offline(self):
        return self.status == self.Status.OFFLINE

    def mark_out_of_order(self):
        self.status = self.Status.OUT_OF_ORDER

    def add_usage(self, hours):
        """Track usage, compute maintenance flag based on service interval."""
        self.total_hours += hours
        self.hours_since_service += hours
        self.needs_service = self.hours_since_service >= settings.SERVICE_INTERVAL_HOURS

    def mark_service_done(self):
        """Reset service hours; an out-of-order treadmill goes OFFLINE until its next heartbeat."""
        self.hours_since_service = 0
        self.needs_service = False
        if self.status == self.Status.OUT_OF_ORDER:
            self.status = self.Status.OFFLINE

    def see(self, ts):
        """Update last_seen timestamp, reject older timestamps. Return True if updated."""
        ts = min(ts, timezone.now())
        if self.last_seen is not None and ts < self.last_seen:
            return False
        self.last_seen = ts
        return True

    def come_back(self, has_live_run):
        """Wake from offline: go IN_USE if an active run exists, otherwise FREE."""
        if self.status != self.Status.OFFLINE:
            return
        if has_live_run:
            self.status = self.Status.IN_USE
        else:
            self.status = self.Status.FREE

    def start_use(self):
        """Mark device in use, ignore if out of order."""
        if self.status in (self.Status.FREE, self.Status.OFFLINE):
            self.status = self.Status.IN_USE

    def finish_use(self):
        """Mark device free, ignore if offline or out of order."""
        if self.status == self.Status.IN_USE:
            self.status = self.Status.FREE

    def go_offline(self):
        """Mark device offline, preserve out-of-order status."""
        if self.status != self.Status.OUT_OF_ORDER:
            self.status = self.Status.OFFLINE


class Alert(models.Model):
    """Safety and maintenance alerts during runs or device issues."""

    class Type(models.TextChoices):
        HR_HIGH = "HR_HIGH", "Heart rate too high"
        NO_HR = "NO_HR", "No heart rate"
        DEVICE_FAULT = "DEVICE_FAULT", "Device fault"

    type = models.CharField(max_length=20, choices=Type.choices)
    message = models.CharField(max_length=300)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="alerts")
    run = models.ForeignKey("runs.Run", on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts")
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["device", "type", "acknowledged_at"])]

    def __str__(self):
        return f"{self.get_type_display()} – {self.device}"

    @property
    def is_open(self):
        return self.acknowledged_at is None

    def acknowledge(self):
        """Mark alert as handled by staff, do nothing if already acknowledged."""
        if self.acknowledged_at is None:
            self.acknowledged_at = timezone.now()
