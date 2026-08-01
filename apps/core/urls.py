"""Rutas públicas y de dashboards."""

from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/client/", views.client_dashboard, name="client_dashboard"),
    path("dashboard/vendor/", views.vendor_dashboard, name="vendor_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
]
