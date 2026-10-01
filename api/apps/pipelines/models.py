from django.db import models
from django.utils import timezone

ERROR_LENGTH = 2000  # max length for error message storage


class PipelineStatus(models.TextChoices):
    RUNNING = "RUNNING", "Running"
    DONE = "DONE", "Done"
    FAILED = "FAILED", "Failed"


class PipelineRun(models.Model):
    """Records execution of a pipeline (e.g., run analysis) with status and timing."""
    class Name(models.TextChoices):
        RUN_ANALYSIS = "run_analysis", "Run analysis"

    name = models.CharField(max_length=20, choices=Name.choices)
    status = models.CharField(max_length=10, choices=PipelineStatus.choices, default=PipelineStatus.RUNNING)
    run = models.ForeignKey("runs.Run", on_delete=models.CASCADE, null=True, blank=True, related_name="pipeline_runs")
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    failed_step = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["-started_at", "-id"]
        indexes = [models.Index(fields=["name", "status", "started_at"])]

    def __str__(self):
        return f"{self.name} #{self.pk} ({self.status})"

    @property
    def duration_ms(self):
        if self.finished_at is None:
            return None
        return round((self.finished_at - self.started_at).total_seconds() * 1000)

    def done(self):
        self.status = PipelineStatus.DONE
        self.finished_at = timezone.now()

    def fail(self, step):
        self.status = PipelineStatus.FAILED
        self.finished_at = timezone.now()
        self.failed_step = step


class PipelineStep(models.Model):
    """Records a single step's status and timing within a pipeline run."""
    pipeline_run = models.ForeignKey(PipelineRun, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=50)
    status = models.CharField(max_length=10, choices=PipelineStatus.choices, default=PipelineStatus.RUNNING)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["pipeline_run", "order"]

    def __str__(self):
        return f"{self.name} of {self.pipeline_run_id}"

    def done(self, duration_ms):
        self.status = PipelineStatus.DONE
        self.duration_ms = duration_ms

    def fail(self, error, duration_ms):
        self.status = PipelineStatus.FAILED
        self.duration_ms = duration_ms
        self.error = str(error)[:ERROR_LENGTH]
