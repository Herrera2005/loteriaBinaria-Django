"""Administración segura del módulo lottery."""

from __future__ import annotations

from django.contrib import admin

from .forms import DrawEventForm, LotteryProductForm
from .models import DrawEvent, DrawResult, LotteryProduct, Ticket


@admin.register(LotteryProduct)
class LotteryProductAdmin(admin.ModelAdmin):
    form = LotteryProductForm
    list_display = (
        "code",
        "name",
        "allowed_symbols",
        "selection_count",
        "is_active",
        "updated_at",
    )
    list_filter = ("code", "is_active")
    search_fields = ("code", "name")
    ordering = ("id",)
    list_per_page = 25
    readonly_fields = ("created_at", "updated_at")

    def has_delete_permission(self, request, obj=None) -> bool:
        if obj is not None and obj.events.exists():
            return False
        return super().has_delete_permission(request, obj)


@admin.register(DrawEvent)
class DrawEventAdmin(admin.ModelAdmin):
    form = DrawEventForm
    list_display = (
        "name",
        "product",
        "status",
        "sales_open_at",
        "sales_close_at",
        "draw_at",
        "price_minor",
        "prize_minor",
    )
    list_filter = ("product", "status", "draw_at")
    search_fields = ("name", "product__name", "product__code")
    ordering = ("draw_at", "id")
    list_select_related = ("product",)
    list_per_page = 25
    readonly_fields = (
        "sales_close_at",
        "created_at",
        "updated_at",
    )

    def has_delete_permission(self, request, obj=None) -> bool:
        if obj is None:
            return False
        if obj.status != DrawEvent.Status.DRAFT:
            return False
        if obj.tickets.exists():
            return False
        try:
            obj.result
        except DrawResult.DoesNotExist:
            return super().has_delete_permission(request, obj)
        return False


class HistoricalReadOnlyAdminMixin:
    """Convierte registros históricos en consultas de solo lectura."""

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_view_permission(self, request, obj=None) -> bool:
        return request.user.is_active and request.user.is_staff


@admin.register(Ticket)
class TicketAdmin(HistoricalReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "operation_id",
        "user",
        "event",
        "normalized_key",
        "price_minor",
        "ownership_status",
        "evaluation_status",
        "award_minor",
        "created_at",
    )
    list_filter = (
        "ownership_status",
        "evaluation_status",
        "event__product",
        "created_at",
    )
    search_fields = (
        "operation_id",
        "normalized_key",
        "user__username",
        "user__email",
        "user__document",
        "event__name",
    )
    ordering = ("-created_at", "-id")
    list_select_related = ("user", "event", "event__product")
    list_per_page = 25
    readonly_fields = (
        "user",
        "event",
        "operation_id",
        "normalized_key",
        "price_minor",
        "ownership_status",
        "evaluation_status",
        "award_minor",
        "credited_at",
        "created_at",
    )


@admin.register(DrawResult)
class DrawResultAdmin(
    HistoricalReadOnlyAdminMixin,
    admin.ModelAdmin,
):
    list_display = (
        "event",
        "winning_key",
        "published_by",
        "published_at",
    )
    list_filter = ("event__product", "published_at")
    search_fields = (
        "event__name",
        "winning_key",
        "published_by__username",
        "published_by__email",
    )
    ordering = ("-published_at", "-id")
    list_select_related = (
        "event",
        "event__product",
        "published_by",
    )
    list_per_page = 25
    readonly_fields = (
        "event",
        "winning_key",
        "published_by",
        "reason",
        "published_at",
    )
