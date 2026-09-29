from django.contrib import admin

from .models import Alert, Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["serial", "status", "needs_service", "hours_since_service", "total_hours", "last_seen"]
    list_filter = ["status", "needs_service"]
    search_fields = ["serial"]


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ["created_at", "type", "device", "message", "acknowledged_at"]
    list_filter = ["type", "acknowledged_at"]
    list_select_related = ["device"]
    readonly_fields = ["created_at"]
