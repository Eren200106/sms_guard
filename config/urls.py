from django.contrib import admin
from django.urls import path, include
from apps.analysis import views as analysis_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("sms/", analysis_views.sms_check, name="sms_check"),
    path("url/", analysis_views.url_check, name="url_check"),
    path("api/v1/", include("apps.analysis.urls")),
]