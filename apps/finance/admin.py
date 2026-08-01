"""Administración de Finance en modo estrictamente read-only."""

from __future__ import annotations

from django.contrib import admin

from .models import Movement, Wallet


class FinanceReadOnlyAdminMixin:
    """Impide CRUD genérico sobre saldos e históricos financieros."""

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_view_permission(self, request, obj=None) -> bool:
        return request.user.is_active and request.user.is_staff


@admin.register(Wallet)
class WalletAdmin(FinanceReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "user",
        "currency",
        "available_minor",
        "reserved_minor",
        "status",
        "updated_at",
    )
    list_filter = ("currency", "status", "updated_at")
    search_fields = (
        "user__username",
        "user__email",
        "user__document",
    )
    ordering = ("user__username", "currency")
    list_select_related = ("user",)
    list_per_page = 25
    readonly_fields = (
        "user",
        "currency",
        "available_minor",
        "reserved_minor",
        "status",
        "created_at",
        "updated_at",
    )


@admin.register(Movement)
class MovementAdmin(FinanceReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "operation_id",
        "wallet",
        "type",
        "direction",
        "amount_minor",
        "balance_after_minor",
        "created_at",
    )
    list_filter = (
        "wallet__currency",
        "type",
        "direction",
        "created_at",
    )
    search_fields = (
        "operation_id",
        "wallet__user__username",
        "wallet__user__email",
        "wallet__user__document",
        "description",
    )
    ordering = ("-created_at", "-id")
    list_select_related = ("wallet", "wallet__user")
    list_per_page = 25
    readonly_fields = (
        "wallet",
        "operation_id",
        "type",
        "direction",
        "amount_minor",
        "balance_after_minor",
        "description",
        "created_at",
    )
