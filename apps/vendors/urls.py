"""Rutas del módulo vendors."""

from django.urls import path

from . import views


app_name = "vendors"

urlpatterns = [
    path(
        "",
        views.VendorProfileListView.as_view(),
        name="vendorprofile_list",
    ),
    path(
        "create/",
        views.VendorProfileCreateView.as_view(),
        name="vendorprofile_create",
    ),
    path(
        "requests/",
        views.ConversionRequestReadOnlyListView.as_view(),
        name="conversionrequest_list",
    ),
    path(
        "<int:pk>/",
        views.VendorProfileDetailView.as_view(),
        name="vendorprofile_detail",
    ),
    path(
        "<int:pk>/edit/",
        views.VendorProfileUpdateView.as_view(),
        name="vendorprofile_update",
    ),
    path(
        "<int:pk>/delete/",
        views.VendorProfileDeleteDeactivateView.as_view(),
        name="vendorprofile_delete",
    ),
]
