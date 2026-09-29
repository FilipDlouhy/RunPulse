from django.contrib import admin

from .models import DeadLetter, PersonalRecord, Run, RunSummary


@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    list_display = ["uuid", "user", "device", "type", "status", "started_at", "ended_at"]
    list_filter = ["status", "type"]
    search_fields = ["uuid", "user__username", "device__serial"]
    list_select_related = ["user", "device"]


@admin.register(RunSummary)
class RunSummaryAdmin(admin.ModelAdmin):
    list_display = ["run", "distance_m", "duration_s", "avg_hr", "trimp", "analyzed_at"]
    list_select_related = ["run"]


@admin.register(PersonalRecord)
class PersonalRecordAdmin(admin.ModelAdmin):
    list_display = ["user", "distance", "time_s", "achieved_at"]
    list_filter = ["distance"]
    list_select_related = ["user"]


@admin.register(DeadLetter)
class DeadLetterAdmin(admin.ModelAdmin):
    list_display = ["created_at", "routing_key", "device_serial", "error"]
    list_filter = ["routing_key"]
    readonly_fields = ["created_at"]
