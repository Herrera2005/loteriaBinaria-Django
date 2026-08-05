"""Modelos del módulo vendors para el Taller #3.

El CRUD evaluable corresponde a ``VendorProfile``. ``ConversionRequest`` y
``ConversionAssignment`` son registros históricos de flujo: usan relaciones
``PROTECT`` y no se exponen a edición genérica de estados.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.accounts.roles import VENDOR
ACTIVE_USER_STATUS = "ACTIVE"


def validate_vendor_account(user, *, require_active: bool = True) -> None:
    """Valida en un único lugar el rol y estado operativo del vendedor."""

    if user is None:
        return

    errors = {}
    if not user.groups.filter(name=VENDOR).exists():
        errors["user"] = (
            "El usuario debe tener asignado el rol VENDEDOR antes de "
            "crear o activar su perfil."
        )
    if require_active and (
        not user.is_active or user.status != ACTIVE_USER_STATUS
    ):
        errors["status"] = (
            "Solo una cuenta de usuario activa puede tener el perfil "
            "vendedor en estado Activo."
        )
    if errors:
        raise ValidationError(errors)


class HistoricalFlowQuerySet(models.QuerySet):
    """Bloquea borrados masivos de solicitudes y asignaciones históricas."""

    def delete(self):
        raise ValidationError(
            "Los registros históricos de solicitudes y asignaciones no se "
            "eliminan."
        )


class VendorProfile(models.Model):
    """Perfil de vendedor, uno a uno con el usuario personalizado."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        ACTIVE = "ACTIVE", "Activo"
        SUSPENDED = "SUSPENDED", "Suspendido"
        DISABLED = "DISABLED", "Desactivado"

    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vendor_profile",
        verbose_name="usuario",
    )
    status = models.CharField(
        "estado",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    activated_at = models.DateTimeField(
        "activado",
        blank=True,
        null=True,
        editable=False,
    )
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ("user__username",)
        indexes = [
            models.Index(
                fields=("status", "created_at"),
                name="vendors_prof_status_date_idx",
            ),
        ]
        verbose_name = "perfil de vendedor"
        verbose_name_plural = "perfiles de vendedores"

    def clean(self) -> None:
        super().clean()

        if not self.user_id:
            return

        requires_valid_vendor = (
            self._state.adding
            or self.status == self.Status.ACTIVE
        )
        if requires_valid_vendor:
            validate_vendor_account(self.user, require_active=True)

    def save(self, *args, **kwargs) -> None:
        if self.status == self.Status.ACTIVE and self.activated_at is None:
            self.activated_at = timezone.now()

            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = tuple(
                    dict.fromkeys((*update_fields, "activated_at"))
                )

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.user} — {self.get_status_display()}"


class ConversionRequest(models.Model):
    """Solicitud histórica de conversión simulada de REAL a VIRTUAL."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        IN_PROGRESS = "IN_PROGRESS", "En proceso"
        COMPLETED_BY_VENDOR = (
            "COMPLETED_BY_VENDOR",
            "Completada por vendedor",
        )
        COMPLETED_BY_PLATFORM = (
            "COMPLETED_BY_PLATFORM",
            "Completada por plataforma",
        )
        CANCELLED = "CANCELLED", "Cancelada"
        EXPIRED = "EXPIRED", "Expirada"
        FAILED_LIQUIDITY = (
            "FAILED_LIQUIDITY",
            "Fallida por liquidez",
        )

    TERMINAL_STATUSES = frozenset(
        {
            Status.COMPLETED_BY_VENDOR,
            Status.COMPLETED_BY_PLATFORM,
            Status.CANCELLED,
            Status.EXPIRED,
            Status.FAILED_LIQUIDITY,
        }
    )

    id = models.BigAutoField(primary_key=True)
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="conversion_requests",
        verbose_name="cliente",
    )
    operation_id = models.UUIDField(
        "identificador de operación",
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    amount_minor = models.BigIntegerField(
        "monto en unidades menores",
        validators=[MinValueValidator(1)],
    )
    status = models.CharField(
        "estado",
        max_length=40,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    expires_at = models.DateTimeField("vence")
    completed_at = models.DateTimeField(
        "completada",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField("creada", auto_now_add=True)
    updated_at = models.DateTimeField("actualizada", auto_now=True)

    objects = HistoricalFlowQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_minor__gt=0),
                name="vendors_request_amount_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(expires_at__gt=F("created_at")),
                name="vendors_req_exp_after_create",
            ),
        ]
        indexes = [
            models.Index(
                fields=("client", "created_at"),
                name="vendors_req_client_date_idx",
            ),
            models.Index(
                fields=("status", "expires_at"),
                name="vendors_req_status_exp_idx",
            ),
        ]
        verbose_name = "solicitud de conversión"
        verbose_name_plural = "solicitudes de conversión"

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Las solicitudes de conversión son históricas y no se eliminan."
        )

    def __str__(self) -> str:
        return f"Solicitud {self.operation_id} — {self.get_status_display()}"


class ConversionAssignment(models.Model):
    """Historial de asignaciones de solicitudes a vendedores."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activa"
        RELEASED = "RELEASED", "Liberada"
        COMPLETED = "COMPLETED", "Completada"
        EXPIRED = "EXPIRED", "Expirada"

    TERMINAL_STATUSES = frozenset(
        {
            Status.RELEASED,
            Status.COMPLETED,
            Status.EXPIRED,
        }
    )

    id = models.BigAutoField(primary_key=True)
    request = models.ForeignKey(
        "vendors.ConversionRequest",
        on_delete=models.PROTECT,
        related_name="assignments",
        verbose_name="solicitud",
    )
    vendor = models.ForeignKey(
        "vendors.VendorProfile",
        on_delete=models.PROTECT,
        related_name="assignments",
        verbose_name="vendedor",
    )
    status = models.CharField(
        "estado",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    assigned_at = models.DateTimeField("asignada", auto_now_add=True)
    released_at = models.DateTimeField(
        "liberada",
        blank=True,
        null=True,
    )
    completed_at = models.DateTimeField(
        "completada",
        blank=True,
        null=True,
    )

    objects = HistoricalFlowQuerySet.as_manager()

    class Meta:
        ordering = ("-assigned_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("request", "vendor", "assigned_at"),
                name="vendors_asg_req_vend_date_uq",
            ),
            models.CheckConstraint(
                condition=(
                    Q(released_at__isnull=True)
                    | Q(released_at__gte=F("assigned_at"))
                ),
                name="vendors_asg_release_after",
            ),
            models.CheckConstraint(
                condition=(
                    Q(completed_at__isnull=True)
                    | Q(completed_at__gte=F("assigned_at"))
                ),
                name="vendors_asg_complete_after",
            ),
        ]
        indexes = [
            models.Index(
                fields=("request", "status"),
                name="vendors_asg_req_status_idx",
            ),
            models.Index(
                fields=("vendor", "status"),
                name="vendors_asg_vendor_status_idx",
            ),
        ]
        verbose_name = "asignación de conversión"
        verbose_name_plural = "asignaciones de conversión"

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Las asignaciones de conversión son históricas y no se eliminan."
        )

    def __str__(self) -> str:
        return (
            f"{self.request.operation_id} → "
            f"{self.vendor.user.username}"
        )
