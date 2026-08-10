from django.urls import path

from .views.vendor import (
    VendorAssignmentDetailView,
    VendorAssignmentListView,
    VendorAvailableRequestListView,
    VendorMovementDetailView,
    VendorMovementListView,
    VendorProfileView,
    VendorWalletDetailView,
    VendorWalletListView,
    VendorAssignRequestView,
    VendorCompleteAssignmentView,
    VendorReleaseAssignmentView,
    VendorInventoryPurchaseDetailView,
    VendorInventoryPurchaseListView,
)


urlpatterns = [
    path(
        "profile/",
        VendorProfileView.as_view(),
        name="v1-vendor-profile",
    ),

    path(
        "wallets/",
        VendorWalletListView.as_view(),
        name="v1-vendor-wallet-list",
    ),
    path(
        "wallets/<int:pk>/",
        VendorWalletDetailView.as_view(),
        name="v1-vendor-wallet-detail",
    ),

    path(
        "movements/",
        VendorMovementListView.as_view(),
        name="v1-vendor-movement-list",
    ),
    path(
        "movements/<int:pk>/",
        VendorMovementDetailView.as_view(),
        name="v1-vendor-movement-detail",
    ),

    path(
        "conversion-requests/available/",
        VendorAvailableRequestListView.as_view(),
        name="v1-vendor-request-available-list",
    ),

    path(
        "assignments/",
        VendorAssignmentListView.as_view(),
        name="v1-vendor-assignment-list",
    ),
    path(
        "assignments/<int:pk>/",
        VendorAssignmentDetailView.as_view(),
        name="v1-vendor-assignment-detail",
    ),
    path(
        "conversion-requests/<int:pk>/assign/",
        VendorAssignRequestView.as_view(),
        name="v1-vendor-request-assign",
    ),

    path(
        "assignments/<int:pk>/complete/",
        VendorCompleteAssignmentView.as_view(),
        name="v1-vendor-assignment-complete",
    ),

    path(
        "assignments/<int:pk>/release/",
        VendorReleaseAssignmentView.as_view(),
        name="v1-vendor-assignment-release",
    ),
    path(
        "inventory-purchases/",
        VendorInventoryPurchaseListView.as_view(),
        name="v1-vendor-inventory-purchase-list",
    ),
    path(
        "inventory-purchases/<int:pk>/",
        VendorInventoryPurchaseDetailView.as_view(),
        name="v1-vendor-inventory-purchase-detail",
    ),
]