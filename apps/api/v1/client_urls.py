from django.urls import path

from .views.client import (
    ClientProfileView,
    ClientTicketDetailView,
    ClientTicketListView,
    ClientWalletDetailView,
    ClientWalletListView,
    ClientMovementDetailView,
    ClientMovementListView,
)


urlpatterns = [
    path(
        "profile/",
        ClientProfileView.as_view(),
        name="v1-client-profile",
    ),

    path(
        "wallets/",
        ClientWalletListView.as_view(),
        name="v1-client-wallet-list",
    ),
    path(
        "wallets/<int:pk>/",
        ClientWalletDetailView.as_view(),
        name="v1-client-wallet-detail",
    ),

    path(
        "tickets/",
        ClientTicketListView.as_view(),
        name="v1-client-ticket-list",
    ),
    path(
        "tickets/<int:pk>/",
        ClientTicketDetailView.as_view(),
        name="v1-client-ticket-detail",
    ),
    path(
        "movements/",
        ClientMovementListView.as_view(),
        name="v1-client-movement-list",
    ),
    path(
        "movements/<int:pk>/",
        ClientMovementDetailView.as_view(),
        name="v1-client-movement-detail",
    ),
]