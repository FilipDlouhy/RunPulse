from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.user.urls")),
    path("api/", include("apps.gym_admin.urls")),
    path("api/", include("apps.runners.urls")),
    path("api/", include("apps.runs.urls")),
    path("api/", include("apps.pipelines.urls")),
    path("", include("apps.realtime.urls")),
]

urlpatterns += staticfiles_urlpatterns()
