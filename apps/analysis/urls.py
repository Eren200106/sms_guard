from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
]

from django.urls import path
from . import views

urlpatterns += [
    path("sms/", views.sms_check, name="sms_check"),
    path("url/", views.url_check, name="url_check"),
]