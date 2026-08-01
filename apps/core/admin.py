"""Administración read-only de la auditoría transversal."""

from __future__ import annotations

from django.contrib import admin

from .models import AuditEvent


class AuditReadOnlyAdminMixin:
    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_view_permission(self, request, obj=None) -> bool:
        return request.user.is_active and request.user.is_staff


@admin.register(AuditEvent)
class AuditEventAdmin(AuditReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "actor",
        "active_mode",
        "action",
        "resource_type",
        "resource_id",
        "created_at",
    )
    list_filter = ("active_mode", "action", "resource_type", "created_at")
    search_fields = (
        "actor__username",
        "actor__email",
        "actor__document",
        "action",
        "resource_type",
        "resource_id",
        "reason",
    )
    ordering = ("-created_at", "-id")
    list_select_related = ("actor",)
    list_per_page = 25
    readonly_fields = (
        "actor",
        "active_mode",
        "action",
        "resource_type",
        "resource_id",
        "reason",
        "metadata",
        "ip_address",
        "created_at",
    )
