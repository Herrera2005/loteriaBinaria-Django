from django.urls import path

from .views.health import HealthView


urlpatterns = [
    path("health/", HealthView.as_view(), name="v1-health"),
]