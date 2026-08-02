"""Rutas de consulta y operaciones financieras."""

from django.urls import path

from . import views


app_name = "finance"

urlpatterns = [
    path("wallets/", views.wallet_detail, name="wallet_detail"),
    path("movements/", views.movement_list, name="movement_list"),
    path(
        "vendor/real-operations/",
        views.vendor_real_operations,
        name="vendor_real_operations",
    ),
    path(
        "vendor/currency-operations/",
        views.vendor_currency_operations,
        name="vendor_currency_operations",
    ),
    path(
        "vendor/inventory/",
        views.vendor_inventory,
        name="vendor_inventory",
    ),
    path(
        "real-operations/",
        views.real_operations,
        name="real_operations",
    ),
    path(
        "wallet-conversion/",
        views.wallet_conversion,
        name="wallet_conversion",
    ),
    path(
        "transfer/",
        views.virtual_transfer,
        name="virtual_transfer",
    ),
    # Compatibilidad con enlaces previos de P-33.
    path("top-up/", views.legacy_topup, name="topup"),
    path("withdraw/", views.legacy_withdrawal, name="withdrawal"),
    path("convert/", views.legacy_conversion, name="conversion"),
]
