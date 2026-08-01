from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from .models import TermsAcceptance, TermsVersion, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Administración segura del usuario personalizado."""

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
    readonly_fields = ("created_at", "updated_at", "last_login", "date_joined")

    fieldsets = UserAdmin.fieldsets + (
        (
            "Datos del Taller #3",
            {
                "fields": (
                    "document",
                    "phone",
                    "birth_date",
                    "status",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Datos del Taller #3",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "document",
                    "phone",
                    "birth_date",
                    "status",
                ),
            },
        ),
    )
    actions = ("activate_selected_users", "deactivate_selected_users")

    @admin.action(description="Activar usuarios seleccionados")
    def activate_selected_users(self, request, queryset):
        updated = queryset.update(status=User.Status.ACTIVE, is_active=True)
        self.message_user(
            request,
            f"{updated} usuario(s) activado(s).",
            level=messages.SUCCESS,
        )

    @admin.action(description="Desactivar usuarios seleccionados")
    def deactivate_selected_users(self, request, queryset):
        protected_ids = list(
            queryset.filter(is_superuser=True).values_list("id", flat=True)
        )
        updated = queryset.exclude(id__in=protected_ids).update(
            status=User.Status.DISABLED,
            is_active=False,
        )
        if protected_ids:
            self.message_user(
                request,
                "Los superusuarios seleccionados no fueron desactivados.",
                level=messages.WARNING,
            )
        self.message_user(
            request,
            f"{updated} usuario(s) desactivado(s).",
            level=messages.SUCCESS,
        )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TermsVersion)
class TermsVersionAdmin(admin.ModelAdmin):
    """Versión legal editable solo antes de recibir aceptaciones."""

    list_display = (
        "kind",
        "version",
        "title",
        "effective_at",
        "is_active",
        "acceptance_count",
    )
    list_filter = ("kind", "is_active", "effective_at")
    search_fields = ("version", "title", "content")
    ordering = ("-effective_at", "-created_at")
    list_per_page = 25
    readonly_fields = ("created_at",)

    @admin.display(description="Aceptaciones")
    def acceptance_count(self, obj):
        return obj.acceptances.count()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("acceptances")

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj is not None and obj.acceptances.exists():
            readonly.extend(
                ("kind", "version", "title", "content", "effective_at")
            )
        return tuple(readonly)

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return False
        return not obj.acceptances.exists()


@admin.register(TermsAcceptance)
class TermsAcceptanceAdmin(admin.ModelAdmin):
    """Histórico de solo lectura."""

    list_display = ("user", "terms_version", "accepted_at", "ip_address")
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
    list_select_related = ("user", "terms_version")
    readonly_fields = ("user", "terms_version", "accepted_at", "ip_address")

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
