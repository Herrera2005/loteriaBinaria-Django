"""Administración segura del módulo vendors."""

from __future__ import annotations

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.roles import VENDOR

from .forms import VendorProfileForm
from .models import (
    ACTIVE_USER_STATUS,
    ConversionAssignment,
    ConversionRequest,
    VendorProfile,
)


User = get_user_model()


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    """CRUD técnico del perfil; el flujo queda separado y protegido."""

    form = VendorProfileForm
    list_display = (
        "user",
        "status",
        "activated_at",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "status",
        "created_at",
        "activated_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__document",
        "user__first_name",
        "user__last_name",
    )
    ordering = ("user__username",)
    list_select_related = ("user",)
    list_per_page = 25
    readonly_fields = (
        "activated_at",
        "created_at",
        "updated_at",
    )
    actions = (
        "activate_selected_profiles",
        "suspend_selected_profiles",
        "disable_selected_profiles",
    )

    @admin.action(description="Activar perfiles seleccionados")
    def activate_selected_profiles(self, request, queryset) -> None:
        activated = 0
        rejected = 0

        for profile in queryset.select_related("user"):
            user_is_valid = (
                profile.user.is_active
                and profile.user.status == ACTIVE_USER_STATUS
                and profile.user.groups.filter(name=VENDOR).exists()
            )
            if not user_is_valid:
                rejected += 1
                continue

            profile.status = VendorProfile.Status.ACTIVE
            if profile.activated_at is None:
                profile.activated_at = timezone.now()
            profile.save(
                update_fields=(
                    "status",
                    "activated_at",
                    "updated_at",
                )
            )
            activated += 1

        if activated:
            self.message_user(
                request,
                f"{activated} perfil(es) activado(s).",
                level=messages.SUCCESS,
            )
        if rejected:
            self.message_user(
                request,
                (
                    f"{rejected} perfil(es) no se activaron porque la cuenta "
                    "no está activa o no conserva el rol VENDEDOR."
                ),
                level=messages.WARNING,
            )

    def _set_non_active_status(
        self,
        *,
        request,
        queryset,
        status: str,
        label: str,
    ) -> None:
        updated = queryset.update(
            status=status,
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            f"{updated} perfil(es) {label}.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Suspender perfiles seleccionados")
    def suspend_selected_profiles(self, request, queryset) -> None:
        self._set_non_active_status(
            request=request,
            queryset=queryset,
            status=VendorProfile.Status.SUSPENDED,
            label="suspendido(s)",
        )

    @admin.action(description="Desactivar perfiles seleccionados")
    def disable_selected_profiles(self, request, queryset) -> None:
        self._set_non_active_status(
            request=request,
            queryset=queryset,
            status=VendorProfile.Status.DISABLED,
            label="desactivado(s)",
        )

    def has_delete_permission(self, request, obj=None) -> bool:
        # La eliminación protegida se implementará en el CRUD visual de P-25.
        return False


class HistoricalFlowAdminMixin:
    """Convierte solicitudes y asignaciones en históricos de solo lectura."""

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_view_permission(self, request, obj=None) -> bool:
        return request.user.is_active and request.user.is_staff


@admin.register(ConversionRequest)
class ConversionRequestAdmin(HistoricalFlowAdminMixin, admin.ModelAdmin):
    list_display = (
        "operation_id",
        "client",
        "amount_minor",
        "status",
        "expires_at",
        "completed_at",
        "created_at",
    )
    list_filter = (
        "status",
        "expires_at",
        "created_at",
    )
    search_fields = (
        "operation_id",
        "client__username",
        "client__email",
        "client__document",
    )
    ordering = ("-created_at", "-id")
    list_select_related = ("client",)
    list_per_page = 25
    readonly_fields = (
        "client",
        "operation_id",
        "amount_minor",
        "status",
        "expires_at",
        "completed_at",
        "created_at",
        "updated_at",
    )


@admin.register(ConversionAssignment)
class ConversionAssignmentAdmin(
    HistoricalFlowAdminMixin,
    admin.ModelAdmin,
):
    list_display = (
        "request",
        "vendor",
        "status",
        "assigned_at",
        "released_at",
        "completed_at",
    )
    list_filter = (
        "status",
        "assigned_at",
        "released_at",
        "completed_at",
    )
    search_fields = (
        "request__operation_id",
        "vendor__user__username",
        "vendor__user__email",
        "vendor__user__document",
    )
    ordering = ("-assigned_at", "-id")
    list_select_related = (
        "request",
        "request__client",
        "vendor",
        "vendor__user",
    )
    list_per_page = 25
    readonly_fields = (
        "request",
        "vendor",
        "status",
        "assigned_at",
        "released_at",
        "completed_at",
    )
