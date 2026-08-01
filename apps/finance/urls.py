"""Rutas read-only del módulo Finance para P-28."""

from django.urls import path

from . import views


app_name = "finance"

urlpatterns = [
    path("wallets/", views.wallet_detail, name="wallet_detail"),
    path("movements/", views.movement_list, name="movement_list"),
]
