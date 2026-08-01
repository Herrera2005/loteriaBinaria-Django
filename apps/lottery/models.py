"""Modelos del módulo lottery para el Taller #3.

LotteryProduct y DrawEvent son los modelos del CRUD evaluable. Ticket y
DrawResult son registros históricos protegidos y no se eliminan mediante CRUD
genérico.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


DRAW_CLOSE_OFFSET = timedelta(minutes=10)


class HistoricalLotteryQuerySet(models.QuerySet):
    """Impide borrado masivo de boletos y resultados históricos."""

    def delete(self):
        raise ValidationError(
            "Los boletos y resultados son históricos y no se eliminan."
        )


class ImmutableResultQuerySet(HistoricalLotteryQuerySet):
    """Impide actualizar resultados por QuerySet."""

    def update(self, **kwargs):
        raise ValidationError(
            "Los resultados publicados son inmutables."
        )


class LotteryProduct(models.Model):
    """Configuración oficial de Octal, Decimal o Hexadecimal."""

    class Code(models.TextChoices):
        OCTAL = "OCTAL", "Octal"
        DECIMAL = "DECIMAL", "Decimal"
        HEXADECIMAL = "HEXADECIMAL", "Hexadecimal"

    PRODUCT_RULES = {
        Code.OCTAL: {
            "allowed_symbols": "01234567",
            "selection_count": 4,
        },
        Code.DECIMAL: {
            "allowed_symbols": "0123456789",
            "selection_count": 5,
        },
        Code.HEXADECIMAL: {
            "allowed_symbols": "0123456789ABCDEF",
            "selection_count": 6,
        },
    }

    id = models.BigAutoField(primary_key=True)
    code = models.CharField(
        "código",
        max_length=20,
        choices=Code.choices,
        unique=True,
    )
    name = models.CharField("nombre", max_length=80)
    allowed_symbols = models.CharField(
        "símbolos permitidos",
        max_length=32,
    )
    selection_count = models.PositiveSmallIntegerField(
        "cantidad de símbolos",
    )
    is_active = models.BooleanField("activo", default=True, db_index=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ("id",)
        constraints = [
            models.CheckConstraint(
                condition=Q(selection_count__gt=0),
                name="lot_prod_selection_gt_0",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        code="OCTAL",
                        allowed_symbols="01234567",
                        selection_count=4,
                    )
                    | Q(
                        code="DECIMAL",
                        allowed_symbols="0123456789",
                        selection_count=5,
                    )
                    | Q(
                        code="HEXADECIMAL",
                        allowed_symbols="0123456789ABCDEF",
                        selection_count=6,
                    )
                ),
                name="lot_prod_valid_config",
            ),
        ]
        verbose_name = "producto de lotería"
        verbose_name_plural = "productos de lotería"

    def clean(self) -> None:
        super().clean()

        rule = self.PRODUCT_RULES.get(self.code)
        if rule is None:
            return

        expected_symbols = rule["allowed_symbols"]
        expected_count = rule["selection_count"]

        if self.allowed_symbols != expected_symbols:
            raise ValidationError(
                {
                    "allowed_symbols": (
                        f"{self.get_code_display()} debe usar exactamente "
                        f"{expected_symbols}."
                    )
                }
            )

        if self.selection_count != expected_count:
            raise ValidationError(
                {
                    "selection_count": (
                        f"{self.get_code_display()} requiere exactamente "
                        f"{expected_count} símbolos únicos."
                    )
                }
            )

    @classmethod
    def rule_for_code(cls, code: str) -> dict[str, object]:
        try:
            return cls.PRODUCT_RULES[code]
        except KeyError as exc:
            raise ValidationError(
                {"code": "El tipo de producto no es válido."}
            ) from exc

    def __str__(self) -> str:
        return self.name


class DrawEvent(models.Model):
    """Evento con cierre exacto diez minutos antes del sorteo."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"
        SCHEDULED = "SCHEDULED", "Programado"
        PUBLISHED = "PUBLISHED", "Publicado"
        SALES_OPEN = "SALES_OPEN", "Ventas abiertas"
        SALES_CLOSED = "SALES_CLOSED", "Ventas cerradas"
        RESULT_SET = "RESULT_SET", "Resultado fijado"
        FINISHED = "FINISHED", "Finalizado"
        CANCELLED = "CANCELLED", "Cancelado"

    id = models.BigAutoField(primary_key=True)
    product = models.ForeignKey(
        "lottery.LotteryProduct",
        on_delete=models.PROTECT,
        related_name="events",
        verbose_name="producto",
    )
    name = models.CharField("nombre", max_length=150)
    sales_open_at = models.DateTimeField("apertura de ventas")
    sales_close_at = models.DateTimeField(
        "cierre de ventas",
        editable=False,
    )
    draw_at = models.DateTimeField("fecha del sorteo")
    price_minor = models.BigIntegerField(
        "precio en unidades menores",
        validators=[MinValueValidator(1)],
    )
    prize_minor = models.BigIntegerField(
        "premio fijo en unidades menores",
        validators=[MinValueValidator(1)],
    )
    status = models.CharField(
        "estado",
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    cancellation_reason = models.TextField(
        "motivo de cancelación",
        blank=True,
    )
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ("draw_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=Q(price_minor__gt=0),
                name="lot_event_price_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(prize_minor__gt=0),
                name="lot_event_prize_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(sales_open_at__lt=F("sales_close_at")),
                name="lot_event_open_before_close",
            ),
            models.CheckConstraint(
                condition=Q(sales_close_at__lt=F("draw_at")),
                name="lot_event_close_before_draw",
            ),
        ]
        indexes = [
            models.Index(
                fields=("product", "status"),
                name="lot_event_prod_status_idx",
            ),
            models.Index(
                fields=("draw_at",),
                name="lot_event_draw_at_idx",
            ),
        ]
        verbose_name = "evento de sorteo"
        verbose_name_plural = "eventos de sorteo"

    @staticmethod
    def calculate_sales_close_at(draw_at):
        if draw_at is None:
            return None
        return draw_at - DRAW_CLOSE_OFFSET

    def clean(self) -> None:
        super().clean()

        if self.draw_at is not None:
            expected_close = self.calculate_sales_close_at(self.draw_at)
            if self.sales_close_at != expected_close:
                raise ValidationError(
                    {
                        "sales_close_at": (
                            "El cierre debe ser exactamente diez minutos "
                            "antes del sorteo."
                        )
                    }
                )

        if (
            self.sales_open_at is not None
            and self.sales_close_at is not None
            and self.sales_open_at >= self.sales_close_at
        ):
            raise ValidationError(
                {
                    "sales_open_at": (
                        "La apertura debe ser anterior al cierre de ventas."
                    )
                }
            )

        if (
            self.status == self.Status.CANCELLED
            and not self.cancellation_reason.strip()
        ):
            raise ValidationError(
                {
                    "cancellation_reason": (
                        "Un evento cancelado requiere un motivo."
                    )
                }
            )

        if (
            self.status != self.Status.CANCELLED
            and self.cancellation_reason.strip()
        ):
            raise ValidationError(
                {
                    "cancellation_reason": (
                        "El motivo solo corresponde a eventos cancelados."
                    )
                }
            )

    def save(self, *args, **kwargs) -> None:
        if self.draw_at is not None:
            self.sales_close_at = self.calculate_sales_close_at(self.draw_at)

            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = tuple(
                    dict.fromkeys((*update_fields, "sales_close_at"))
                )

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} — {timezone.localtime(self.draw_at):%Y-%m-%d %H:%M}"


def normalize_lottery_key(value: str) -> str:
    """Normaliza una combinación sin aceptar separadores internos."""
    return (value or "").strip().upper()


def validate_key_for_product(
    *,
    value: str,
    product: LotteryProduct,
    field_name: str,
) -> str:
    """Valida longitud, símbolos permitidos y ausencia de repetidos."""
    normalized = normalize_lottery_key(value)

    if len(normalized) != product.selection_count:
        raise ValidationError(
            {
                field_name: (
                    f"La combinación debe contener exactamente "
                    f"{product.selection_count} símbolos."
                )
            }
        )

    invalid_symbols = sorted(
        set(normalized) - set(product.allowed_symbols)
    )
    if invalid_symbols:
        raise ValidationError(
            {
                field_name: (
                    "La combinación contiene símbolos no permitidos: "
                    f"{', '.join(invalid_symbols)}."
                )
            }
        )

    if len(set(normalized)) != len(normalized):
        raise ValidationError(
            {
                field_name: (
                    "Los símbolos de la combinación deben ser únicos."
                )
            }
        )

    return normalized


class Ticket(models.Model):
    """Boleto histórico comprado por un cliente."""

    class OwnershipStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Activo"
        REFUNDED = "REFUNDED", "Reembolsado"
        CANCELLED = "CANCELLED", "Cancelado"

    class EvaluationStatus(models.TextChoices):
        PENDING_RESULT = "PENDING_RESULT", "Pendiente de resultado"
        NOT_WINNER = "NOT_WINNER", "No ganador"
        REFUND = "REFUND", "Reembolso"
        WINNER = "WINNER", "Ganador"

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="cliente",
    )
    event = models.ForeignKey(
        "lottery.DrawEvent",
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="evento",
    )
    operation_id = models.UUIDField(
        "identificador de operación",
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    normalized_key = models.CharField(
        "combinación normalizada",
        max_length=16,
    )
    price_minor = models.BigIntegerField(
        "precio en unidades menores",
        validators=[MinValueValidator(1)],
    )
    ownership_status = models.CharField(
        "estado de propiedad",
        max_length=20,
        choices=OwnershipStatus.choices,
        default=OwnershipStatus.ACTIVE,
        db_index=True,
    )
    evaluation_status = models.CharField(
        "estado de evaluación",
        max_length=30,
        choices=EvaluationStatus.choices,
        default=EvaluationStatus.PENDING_RESULT,
        db_index=True,
    )
    award_minor = models.BigIntegerField(
        "premio acreditado en unidades menores",
        default=0,
        validators=[MinValueValidator(0)],
    )
    credited_at = models.DateTimeField(
        "acreditado",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField("creado", auto_now_add=True)

    objects = HistoricalLotteryQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("event", "normalized_key"),
                name="lot_ticket_event_key_uq",
            ),
            models.CheckConstraint(
                condition=Q(price_minor__gt=0),
                name="lot_ticket_price_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(award_minor__gte=0),
                name="lot_ticket_award_gte_0",
            ),
        ]
        indexes = [
            models.Index(
                fields=("user", "created_at"),
                name="lot_ticket_user_date_idx",
            ),
            models.Index(
                fields=("event", "evaluation_status"),
                name="lot_ticket_event_eval_idx",
            ),
        ]
        verbose_name = "boleto"
        verbose_name_plural = "boletos"

    def clean(self) -> None:
        super().clean()

        if not self.event_id:
            return

        self.normalized_key = validate_key_for_product(
            value=self.normalized_key,
            product=self.event.product,
            field_name="normalized_key",
        )

        if self.price_minor != self.event.price_minor:
            raise ValidationError(
                {
                    "price_minor": (
                        "El precio histórico del boleto debe coincidir con "
                        "el precio fijo del evento al crearlo."
                    )
                }
            )

    def save(self, *args, **kwargs) -> None:
        self.normalized_key = normalize_lottery_key(
            self.normalized_key
        )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Los boletos son históricos y no se eliminan."
        )

    def __str__(self) -> str:
        return f"{self.normalized_key} — {self.event.name}"


class DrawResult(models.Model):
    """Resultado único, protegido e inmutable de un evento."""

    id = models.BigAutoField(primary_key=True)
    event = models.OneToOneField(
        "lottery.DrawEvent",
        on_delete=models.PROTECT,
        related_name="result",
        verbose_name="evento",
    )
    winning_key = models.CharField(
        "combinación ganadora",
        max_length=16,
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="published_draw_results",
        verbose_name="publicado por",
    )
    reason = models.TextField("motivo")
    published_at = models.DateTimeField(
        "publicado",
        auto_now_add=True,
    )

    objects = ImmutableResultQuerySet.as_manager()

    class Meta:
        ordering = ("-published_at", "-id")
        indexes = [
            models.Index(
                fields=("published_at",),
                name="lot_result_published_idx",
            ),
        ]
        verbose_name = "resultado de sorteo"
        verbose_name_plural = "resultados de sorteo"

    def clean(self) -> None:
        super().clean()

        if not self.event_id:
            return

        self.winning_key = validate_key_for_product(
            value=self.winning_key,
            product=self.event.product,
            field_name="winning_key",
        )

        if not self.reason.strip():
            raise ValidationError(
                {"reason": "La publicación requiere un motivo."}
            )

        if self.event.status == DrawEvent.Status.CANCELLED:
            raise ValidationError(
                {
                    "event": (
                        "No se puede publicar resultado de un evento "
                        "cancelado."
                    )
                }
            )

    def save(self, *args, **kwargs) -> None:
        if self.pk is not None:
            raise ValidationError(
                "El resultado publicado es inmutable."
            )

        self.winning_key = normalize_lottery_key(
            self.winning_key
        )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Los resultados publicados son históricos y no se eliminan."
        )

    def __str__(self) -> str:
        return f"{self.event.name}: {self.winning_key}"
