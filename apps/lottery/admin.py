"""Administración segura del módulo lottery."""

from __future__ import annotations

from django.contrib import admin

from .forms import DrawEventForm, LotteryProductForm
from .models import (
    DrawEvent,
    DrawEventSeries,
    DrawEventStatusTransition,
    DrawResult,
    LotteryProduct,
    Ticket,
)


@admin.register(LotteryProduct)
class LotteryProductAdmin(admin.ModelAdmin):
    form = LotteryProductForm
    list_display = (
        "kind",
        "code",
        "name",
        "symbol_universe",
        "selection_count",
        "is_active",
        "updated_at",
    )
    list_filter = ("kind", "is_active")
    search_fields = ("code", "name")
    ordering = ("id",)
    list_per_page = 25
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Símbolos")
    def symbol_universe(self, obj):
        return obj.symbol_universe_display

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
        "award_operation_id",
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
        "publication_source",
        "published_by",
        "published_at",
    )
    list_filter = ("publication_source", "event__product", "published_at")
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
        "publication_source",
        "published_by",
        "reason",
        "published_at",
    )


@admin.register(DrawEventStatusTransition)
class DrawEventStatusTransitionAdmin(HistoricalReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "event",
        "from_status",
        "to_status",
        "changed_by",
        "created_at",
    )
    list_filter = ("from_status", "to_status", "created_at")
    search_fields = ("event__name", "reason", "public_message")
    list_select_related = ("event", "changed_by")
    ordering = ("-created_at", "-id")
    readonly_fields = (
        "event",
        "from_status",
        "to_status",
        "reason",
        "public_message",
        "changed_by",
        "created_at",
    )


@admin.register(DrawEventSeries)
class DrawEventSeriesAdmin(admin.ModelAdmin):
    list_display = (
        "name_prefix",
        "product",
        "recurrence_minutes",
        "future_events_target",
        "remaining_occurrences",
        "result_mode",
        "next_sequence",
        "next_draw_at",
        "is_active",
        "is_archived",
    )
    list_filter = ("result_mode", "is_active", "is_archived", "product")
    search_fields = ("name_prefix", "product__name", "product__code")
    readonly_fields = ("next_sequence", "archived_at", "created_at", "updated_at")
    list_select_related = ("product", "created_by")

    def has_delete_permission(self, request, obj=None):
        return False
