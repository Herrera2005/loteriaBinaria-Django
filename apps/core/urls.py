"""Rutas públicas, redirección inicial, dashboards y auditoría read-only."""

from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("start/", views.start_redirect, name="start"),
    path("dashboard/client/", views.client_dashboard, name="client_dashboard"),
    path("dashboard/vendor/", views.vendor_dashboard, name="vendor_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("audit/", views.audit_list, name="audit_list"),
    path("audit/<int:pk>/", views.audit_detail, name="audit_detail"),
]