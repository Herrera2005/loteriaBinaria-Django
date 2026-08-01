"""Modelos financieros base del Taller #3.

``Wallet`` mantiene saldos por moneda. ``Movement`` es un histórico
append-only y correlacionado mediante ``operation_id``. En esta preparación
P-28A no se implementan recargas, conversiones ni otras operaciones de saldo.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class CurrencyCode(models.TextChoices):
    """Monedas separadas definidas por las reglas canónicas."""

    REAL = "REAL", "REAL"
    VIRTUAL = "VIRTUAL", "VIRTUAL"


class Wallet(models.Model):
    """Wallet separada por usuario y moneda, sin formularios CRUD genéricos."""

    Currency = CurrencyCode

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activa"
        SUSPENDED = "SUSPENDED", "Suspendida"
        BLOCKED = "BLOCKED", "Bloqueada"
        DISABLED = "DISABLED", "Desactivada"

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="wallets",
        verbose_name="usuario",
    )
    currency = models.CharField(
        "moneda",
        max_length=10,
        choices=CurrencyCode.choices,
    )
    available_minor = models.BigIntegerField(
        "saldo disponible en unidades menores",
        default=0,
        validators=[MinValueValidator(0)],
    )
    reserved_minor = models.BigIntegerField(
        "saldo reservado en unidades menores",
        default=0,
        validators=[MinValueValidator(0)],
    )
    status = models.CharField(
        "estado",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    created_at = models.DateTimeField("creada", auto_now_add=True)
    updated_at = models.DateTimeField("actualizada", auto_now=True)

    class Meta:
        ordering = ("user__username", "currency")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "currency"),
                name="fin_wallet_user_curr_uq",
            ),
            models.CheckConstraint(
                condition=Q(available_minor__gte=0),
                name="fin_wallet_available_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(reserved_minor__gte=0),
                name="fin_wallet_reserved_gte_0",
            ),
        ]
        indexes = [
            models.Index(
                fields=("user", "status"),
                name="fin_wallet_user_status_idx",
            ),
            models.Index(
                fields=("currency", "status"),
                name="fin_wallet_curr_status_idx",
            ),
        ]
        verbose_name = "wallet"
        verbose_name_plural = "wallets"

    def clean(self) -> None:
        super().clean()

        errors = {}
        if self.available_minor < 0:
            errors["available_minor"] = (
                "El saldo disponible no puede ser negativo."
            )
        if self.reserved_minor < 0:
            errors["reserved_minor"] = (
                "El saldo reservado no puede ser negativo."
            )
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"{self.user} — {self.currency}"


class HistoricalMovementQuerySet(models.QuerySet):
    """Bloquea cambios y eliminaciones masivas del histórico financiero."""

    def update(self, **kwargs):
        raise ValidationError("Los movimientos históricos no se editan.")

    def delete(self):
        raise ValidationError("Los movimientos históricos no se eliminan.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("Los movimientos históricos no se editan.")


class Movement(models.Model):
    """Efecto visible e inmutable producido por una operación financiera."""

    class Type(models.TextChoices):
        TOP_UP = "TOP_UP", "Recarga REAL simulada"
        VIRTUAL_TO_REAL = "VIRTUAL_TO_REAL", "Conversión VIRTUAL a REAL"
        VIRTUAL_TRANSFER = "VIRTUAL_TRANSFER", "Transferencia VIRTUAL"
        WHOLESALE_PURCHASE = "WHOLESALE_PURCHASE", "Compra mayorista"
        CONVERSION_REQUEST = "CONVERSION_REQUEST", "Solicitud de conversión"
        TICKET_PURCHASE = "TICKET_PURCHASE", "Compra de boleto"
        PRIZE = "PRIZE", "Premio"
        REFUND = "REFUND", "Reembolso"
        WITHDRAWAL = "WITHDRAWAL", "Retiro simulado"
        ADJUSTMENT = "ADJUSTMENT", "Ajuste administrativo"

    class Direction(models.TextChoices):
        CREDIT = "CREDIT", "Crédito"
        DEBIT = "DEBIT", "Débito"

    id = models.BigAutoField(primary_key=True)
    wallet = models.ForeignKey(
        "finance.Wallet",
        on_delete=models.PROTECT,
        related_name="movements",
        verbose_name="wallet",
    )
    operation_id = models.UUIDField(
        "identificador de operación",
        default=uuid.uuid4,
        editable=False,
        db_index=True,
    )
    type = models.CharField(
        "tipo",
        max_length=40,
        choices=Type.choices,
        db_index=True,
    )
    direction = models.CharField(
        "dirección",
        max_length=10,
        choices=Direction.choices,
    )
    amount_minor = models.BigIntegerField(
        "monto en unidades menores",
        validators=[MinValueValidator(1)],
    )
    balance_after_minor = models.BigIntegerField(
        "saldo posterior en unidades menores",
        validators=[MinValueValidator(0)],
    )
    description = models.CharField(
        "descripción",
        max_length=255,
        blank=True,
    )
    created_at = models.DateTimeField("creado", auto_now_add=True)

    objects = HistoricalMovementQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_minor__gt=0),
                name="fin_move_amount_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(balance_after_minor__gte=0),
                name="fin_move_balance_gte_0",
            ),
        ]
        indexes = [
            models.Index(
                fields=("wallet", "created_at"),
                name="fin_move_wallet_date_idx",
            ),
            models.Index(
                fields=("type", "created_at"),
                name="fin_move_type_date_idx",
            ),
        ]
        verbose_name = "movimiento"
        verbose_name_plural = "movimientos"

    def save(self, *args, **kwargs) -> None:
        if self.pk and type(self)._base_manager.filter(pk=self.pk).exists():
            raise ValidationError("Los movimientos históricos no se editan.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Los movimientos históricos no se eliminan.")

    def __str__(self) -> str:
        return f"{self.operation_id} — {self.get_type_display()}"
