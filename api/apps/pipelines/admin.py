from django.contrib import admin

from .models import PipelineRun, PipelineStep


class PipelineStepInline(admin.TabularInline):
    model = PipelineStep
    extra = 0


@admin.register(PipelineRun)
class PipelineRunAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "status", "run", "started_at", "failed_step"]
    list_filter = ["name", "status"]
    inlines = [PipelineStepInline]
