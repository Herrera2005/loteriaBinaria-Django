"""Configuración administrativa del módulo accounts."""

from __future__ import annotations

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from .forms import (
    TermsVersionForm,
    UserAdminChangeForm,
    UserAdminCreationForm,
)
from .models import TermsAcceptance, TermsVersion, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """CRUD seguro de usuarios con desactivación en lugar de borrado."""

    add_form = UserAdminCreationForm
    form = UserAdminChangeForm
    model = User

    list_display = (
        "username",
        "email",
        "document",
        "status",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    list_filter = (
        "status",
        "is_active",
        "is_staff",
        "is_superuser",
        "groups",
    )
    search_fields = (
        "username",
        "email",
        "document",
        "first_name",
        "last_name",
    )
    ordering = ("username",)
    list_per_page = 25
    filter_horizontal = ("groups", "user_permissions")
    readonly_fields = (
        "created_at",
        "updated_at",
        "last_login",
        "date_joined",
    )

    fieldsets = (
        (
            "Credenciales",
            {
                "fields": (
                    "username",
                    "password",
                ),
            },
        ),
        (
            "Datos personales",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "document",
                    "phone",
                    "birth_date",
                ),
            },
        ),
        (
            "Estado de la cuenta",
            {
                "fields": (
                    "status",
                    "is_active",
                ),
                "description": (
                    "Las cuentas no se eliminan. Para retirar el acceso, "
                    "seleccione un estado no activo y desmarque Acceso "
                    "habilitado."
                ),
            },
        ),
        (
            "Roles y permisos",
            {
                "fields": (
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Fechas",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    add_fieldsets = (
        (
            "Credenciales",
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                ),
            },
        ),
        (
            "Datos personales",
            {
                "classes": ("wide",),
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "document",
                    "phone",
                    "birth_date",
                ),
            },
        ),
        (
            "Estado y permisos",
            {
                "classes": ("wide",),
                "fields": (
                    "status",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )

    actions = (
        "activate_selected_users",
        "suspend_selected_users",
        "block_selected_users",
        "deactivate_selected_users",
    )

    @admin.action(description="Activar usuarios seleccionados")
    def activate_selected_users(self, request, queryset) -> None:
        updated = queryset.update(
            status=User.Status.ACTIVE,
            is_active=True,
        )
        self.message_user(
            request,
            f"{updated} usuario(s) activado(s).",
            level=messages.SUCCESS,
        )

    def _deactivate_with_status(
        self,
        *,
        request,
        queryset,
        status: str,
        label: str,
    ) -> None:
        protected_ids = list(
            queryset.filter(is_superuser=True).values_list("id", flat=True)
        )
        safe_queryset = queryset.exclude(id__in=protected_ids)
        updated = safe_queryset.update(
            status=status,
            is_active=False,
        )

        if protected_ids:
            self.message_user(
                request,
                (
                    "Los superusuarios seleccionados no fueron modificados "
                    "por esta acción masiva."
                ),
                level=messages.WARNING,
            )

        self.message_user(
            request,
            f"{updated} usuario(s) {label}.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Suspender usuarios seleccionados")
    def suspend_selected_users(self, request, queryset) -> None:
        self._deactivate_with_status(
            request=request,
            queryset=queryset,
            status=User.Status.SUSPENDED,
            label="suspendido(s)",
        )

    @admin.action(description="Bloquear usuarios seleccionados")
    def block_selected_users(self, request, queryset) -> None:
        self._deactivate_with_status(
            request=request,
            queryset=queryset,
            status=User.Status.BLOCKED,
            label="bloqueado(s)",
        )

    @admin.action(description="Desactivar usuarios seleccionados")
    def deactivate_selected_users(self, request, queryset) -> None:
        self._deactivate_with_status(
            request=request,
            queryset=queryset,
            status=User.Status.DISABLED,
            label="desactivado(s)",
        )

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(TermsVersion)
class TermsVersionAdmin(admin.ModelAdmin):
    """CRUD legal: las versiones se desactivan y nunca se eliminan."""

    form = TermsVersionForm

    list_display = (
        "kind",
        "version",
        "title",
        "effective_at",
        "is_active",
        "acceptance_count",
    )
    list_filter = (
        "kind",
        "is_active",
        "effective_at",
    )
    search_fields = (
        "version",
        "title",
        "content",
    )
    ordering = ("-effective_at", "-created_at")
    list_per_page = 25
    readonly_fields = ("created_at",)
    actions = (
        "activate_selected_versions",
        "deactivate_selected_versions",
    )

    @admin.display(description="Aceptaciones")
    def acceptance_count(self, obj) -> int:
        return obj.acceptances.count()

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("acceptances")
        )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj is not None and obj.acceptances.exists():
            readonly.extend(TermsVersion.IMMUTABLE_AFTER_ACCEPTANCE)
        return tuple(dict.fromkeys(readonly))

    @admin.action(description="Activar versiones seleccionadas")
    def activate_selected_versions(self, request, queryset) -> None:
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"{updated} versión(es) activada(s).",
            level=messages.SUCCESS,
        )

    @admin.action(description="Desactivar versiones seleccionadas")
    def deactivate_selected_versions(self, request, queryset) -> None:
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} versión(es) desactivada(s).",
            level=messages.SUCCESS,
        )

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(TermsAcceptance)
class TermsAcceptanceAdmin(admin.ModelAdmin):
    """Histórico legal de solo lectura."""

    list_display = (
        "user",
        "terms_version",
        "accepted_at",
        "ip_address",
    )
    list_filter = (
        "terms_version__kind",
        "terms_version__version",
        "accepted_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__document",
        "terms_version__title",
    )
    ordering = ("-accepted_at",)
    list_per_page = 25
    list_select_related = (
        "user",
        "terms_version",
    )
    readonly_fields = (
        "user",
        "terms_version",
        "accepted_at",
        "ip_address",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_view_permission(self, request, obj=None) -> bool:
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False