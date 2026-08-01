"""Enrutamiento raíz del Taller #3."""

from django.contrib import admin
from django.urls import include, path


admin.site.site_header = "Lotería Binaria — Administración"
admin.site.site_title = "Lotería Binaria"
admin.site.index_title = "Simulación académica"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
    path("vendors/", include("apps.vendors.urls")),
    path("lottery/", include("apps.lottery.urls")),
]
