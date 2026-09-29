from django.contrib import admin

from .models import RunnerProfile


@admin.register(RunnerProfile)
class RunnerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "birth_date", "hr_rest", "hr_max", "goal_distance"]
    list_select_related = ["user"]
