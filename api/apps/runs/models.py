import json
import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.gym_admin.models import Device


class RunType(models.TextChoices):
    EASY = "easy", "Easy"
    INTERVALS = "intervals", "Intervals"
    TEMPO = "tempo", "Tempo"
    LONG = "long", "Long"


class Run(models.Model):
    class Status(models.TextChoices):
        LIVE = "LIVE", "Live"
        ANALYZING = "ANALYZING", "Analyzing"
        DONE = "DONE", "Done"
        FAILED = "FAILED", "Failed"

    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="runs")
    device = models.ForeignKey(Device, on_delete=models.PROTECT, related_name="runs")
    type = models.CharField(max_length=20, choices=RunType.choices)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.LIVE)
    last_data_at = models.DateTimeField(default=timezone.now)
    rpe = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["user", "-started_at"]),
            models.Index(fields=["device", "started_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.get_type_display()} run of {self.user} on {self.device}"

    @property
    def is_live(self):
        return self.status == self.Status.LIVE

    def end(self, ts):
        self.ended_at = ts
        self.status = self.Status.ANALYZING

    def finish_analysis(self):
        self.status = self.Status.DONE

    def fail_analysis(self):
        self.status = self.Status.FAILED


class Sample(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="samples")
    seq = models.PositiveIntegerField()
    time = models.DateTimeField()
    hr = models.PositiveSmallIntegerField(null=True, blank=True)
    speed_kmh = models.FloatField()
    incline = models.FloatField()

    class Meta:
        ordering = ["run", "seq"]
        indexes = [models.Index(fields=["run", "time"])]
        constraints = [models.UniqueConstraint(fields=["run", "seq", "time"], name="unique_sample_seq")]

    def __str__(self):
        return f"#{self.seq} of {self.run_id}"


class RunSummary(models.Model):
    run = models.OneToOneField(Run, on_delete=models.CASCADE, related_name="summary")
    distance_m = models.PositiveIntegerField()
    duration_s = models.PositiveIntegerField()
    avg_pace_s = models.PositiveIntegerField(null=True, blank=True)
    avg_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    max_hr = models.PositiveSmallIntegerField(null=True, blank=True)
    zones = models.JSONField(default=list, blank=True)
    splits = models.JSONField(default=list, blank=True)
    trimp = models.PositiveIntegerField(default=0)
    kcal = models.PositiveIntegerField(default=0)
    cleaned_points = models.PositiveIntegerField(default=0)
    analyzed_at = models.DateTimeField()

    class Meta:
        verbose_name_plural = "run summaries"

    def __str__(self):
        return f"Summary of run {self.run_id}"


class RecordDistance(models.TextChoices):
    K1 = "1K", "1 km"
    K5 = "5K", "5 km"
    K10 = "10K", "10 km"


RECORD_METERS = {
    RecordDistance.K1: 1000,
    RecordDistance.K5: 5000,
    RecordDistance.K10: 10000,
}


class PersonalRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="records")
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="records")
    distance = models.CharField(max_length=10, choices=RecordDistance.choices)
    time_s = models.PositiveIntegerField()
    achieved_at = models.DateTimeField()

    class Meta:
        ordering = ["distance", "time_s"]
        constraints = [models.UniqueConstraint(fields=["run", "distance"], name="unique_run_record")]
        indexes = [models.Index(fields=["user", "distance", "time_s"])]

    def __str__(self):
        return f"{self.get_distance_display()} in {self.time_s} s by {self.user}"

    @property
    def meters(self):
        return RECORD_METERS[self.distance]

    @property
    def pace_s(self):
        return round(self.time_s / (self.meters / 1000))


HEALTH_FIELDS = {"hr"}
REDACTED_BODY_LENGTH = 500


class DeadLetter(models.Model):
    routing_key = models.CharField(max_length=50, blank=True)
    body = models.TextField(blank=True)
    error = models.TextField()
    device_serial = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.routing_key or 'unknown'}: {self.error[:60]}"

    @property
    def redacted_body(self):
        try:
            data = json.loads(self.body)
        except ValueError:
            return self.body[:REDACTED_BODY_LENGTH]
        if not isinstance(data, dict):
            return self.body[:REDACTED_BODY_LENGTH]
        safe_data = {}
        for key, value in data.items():
            if key not in HEALTH_FIELDS:
                safe_data[key] = value
        return json.dumps(safe_data)


class UsageHourly(models.Model):
    pk = models.CompositePrimaryKey("bucket", "run")
    bucket = models.DateTimeField()
    run = models.ForeignKey(Run, on_delete=models.DO_NOTHING, related_name="+")
    seconds = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = "usage_hourly"

    def __str__(self):
        return f"{self.bucket} run {self.run_id}: {self.seconds}s"
