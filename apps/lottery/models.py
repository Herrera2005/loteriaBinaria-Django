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
from django.core.validators import MinValueValidator, RegexValidator
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


class LotteryProductQuerySet(models.QuerySet):
    """Evita alterar en masa la configuración estructural del producto."""

    PROTECTED_FIELDS = {
        "kind",
        "code",
        "allowed_symbols",
        "selection_count",
    }

    def update(self, **kwargs):
        if self.PROTECTED_FIELDS.intersection(kwargs):
            raise ValidationError(
                "La configuración estructural del producto no se actualiza "
                "mediante QuerySet.update()."
            )
        return super().update(**kwargs)


SYMBOL_TOKEN_SEPARATOR = "|"
MAX_SYMBOL_TOKEN_LENGTH = 2
MAX_PRODUCT_SYMBOLS = 32


def _normalize_symbol_token(value: object) -> str:
    return str(value or "").strip().upper()


def _split_symbol_storage(value: str) -> tuple[str, ...]:
    """Lee el almacenamiento actual y el legado de un carácter por símbolo."""
    raw = (value or "").strip().upper()
    if not raw:
        return ()
    if SYMBOL_TOKEN_SEPARATOR in raw:
        return tuple(part.strip() for part in raw.split(SYMBOL_TOKEN_SEPARATOR))
    return tuple(raw)


def _serialize_symbol_tokens(tokens) -> str:
    return SYMBOL_TOKEN_SEPARATOR.join(_normalize_symbol_token(token) for token in tokens)


class LotteryProduct(models.Model):
    """Producto oficial o personalizado de la lotería."""

    class Kind(models.TextChoices):
        OFFICIAL = "OFFICIAL", "Oficial"
        CUSTOM = "CUSTOM", "Personalizado"

    class Code(models.TextChoices):
        OCTAL = "OCTAL", "Octal"
        DECIMAL = "DECIMAL", "Decimal"
        HEXADECIMAL = "HEXADECIMAL", "Hexadecimal"

    CODE_VALIDATOR = RegexValidator(
        regex=r"^[A-Z0-9_]+$",
        message=(
            "El código solo puede contener letras, números y guion bajo."
        ),
    )

    IMMUTABLE_WITH_EVENTS_FIELDS = (
        "kind",
        "code",
        "allowed_symbols",
        "selection_count",
    )

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
    kind = models.CharField(
        "tipo de configuración",
        max_length=12,
        choices=Kind.choices,
        default=Kind.OFFICIAL,
        db_index=True,
    )
    code = models.CharField(
        "código",
        max_length=20,
        unique=True,
        validators=[CODE_VALIDATOR],
    )
    name = models.CharField("nombre", max_length=80)
    allowed_symbols = models.CharField(
        "símbolos permitidos",
        max_length=95,
    )
    selection_count = models.PositiveSmallIntegerField(
        "cantidad de posiciones",
    )
    is_active = models.BooleanField("activo", default=True, db_index=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    objects = LotteryProductQuerySet.as_manager()

    class Meta:
        ordering = ("id",)
        constraints = [
            models.CheckConstraint(
                condition=Q(selection_count__gte=2, selection_count__lte=8),
                name="lot_prod_selection_2_8",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        kind="OFFICIAL",
                        code="OCTAL",
                        allowed_symbols="01234567",
                        selection_count=4,
                    )
                    | Q(
                        kind="OFFICIAL",
                        code="DECIMAL",
                        allowed_symbols="0123456789",
                        selection_count=5,
                    )
                    | Q(
                        kind="OFFICIAL",
                        code="HEXADECIMAL",
                        allowed_symbols="0123456789ABCDEF",
                        selection_count=6,
                    )
                    | (
                        Q(kind="CUSTOM")
                        & ~Q(code__in=("OCTAL", "DECIMAL", "HEXADECIMAL"))
                    )
                ),
                name="lot_prod_valid_config",
            ),
        ]
        verbose_name = "producto de lotería"
        verbose_name_plural = "productos de lotería"

    @property
    def symbol_tokens(self) -> tuple[str, ...]:
        """Universo de símbolos como tokens independientes."""
        if self.kind == self.Kind.OFFICIAL:
            return tuple((self.allowed_symbols or "").strip().upper())
        return _split_symbol_storage(self.allowed_symbols)

    @property
    def symbol_universe_display(self) -> str:
        return " · ".join(self.symbol_tokens)

    @property
    def symbol_count(self) -> int:
        return len(self.symbol_tokens)

    @classmethod
    def serialize_symbol_tokens(cls, tokens) -> str:
        return _serialize_symbol_tokens(tokens)

    @classmethod
    def parse_symbol_storage(cls, value: str) -> tuple[str, ...]:
        return _split_symbol_storage(value)

    def key_tokens(self, value: str) -> tuple[str, ...]:
        return split_lottery_key(value=value, product=self)

    def _validate_persisted_immutability(self) -> None:
        if not self.pk or not self.events.exists():
            return

        original = (
            type(self).objects
            .filter(pk=self.pk)
            .only(*self.IMMUTABLE_WITH_EVENTS_FIELDS)
            .first()
        )
        if original is None:
            return

        changed_fields = [
            field_name
            for field_name in self.IMMUTABLE_WITH_EVENTS_FIELDS
            if getattr(self, field_name) != getattr(original, field_name)
        ]
        if changed_fields:
            raise ValidationError(
                "Un producto con eventos no permite cambiar su tipo, código, "
                "símbolos ni cantidad de posiciones."
            )

    def clean(self) -> None:
        super().clean()

        self.kind = (self.kind or "").strip().upper()
        self.code = (self.code or "").strip().upper()

        self._validate_persisted_immutability()

        if not self.code:
            raise ValidationError({"code": "El código es obligatorio."})

        self.CODE_VALIDATOR(self.code)

        if self.kind == self.Kind.OFFICIAL:
            self.allowed_symbols = (self.allowed_symbols or "").strip().upper()
            rule = self.PRODUCT_RULES.get(self.code)
            if rule is None:
                raise ValidationError(
                    {"code": "Seleccione Octal, Decimal o Hexadecimal."}
                )

            expected_symbols = rule["allowed_symbols"]
            expected_count = rule["selection_count"]

            if self.allowed_symbols != expected_symbols:
                raise ValidationError(
                    {
                        "allowed_symbols": (
                            f"{dict(self.Code.choices)[self.code]} debe usar exactamente "
                            f"{expected_symbols}."
                        )
                    }
                )

            if self.selection_count != expected_count:
                raise ValidationError(
                    {
                        "selection_count": (
                            f"{dict(self.Code.choices)[self.code]} requiere exactamente "
                            f"{expected_count} posiciones."
                        )
                    }
                )
            return

        if self.kind != self.Kind.CUSTOM:
            raise ValidationError(
                {"kind": "El tipo de configuración no es válido."}
            )

        if self.code in self.PRODUCT_RULES:
            raise ValidationError(
                {
                    "code": (
                        "Los códigos OCTAL, DECIMAL y HEXADECIMAL están "
                        "reservados para productos oficiales."
                    )
                }
            )

        tokens = tuple(_normalize_symbol_token(token) for token in self.symbol_tokens)
        self.allowed_symbols = _serialize_symbol_tokens(tokens)

        if not tokens or any(not token for token in tokens):
            raise ValidationError(
                {"allowed_symbols": "Ingrese al menos dos símbolos separados."}
            )

        invalid_tokens = [
            token
            for token in tokens
            if not token.isalnum() or len(token) > MAX_SYMBOL_TOKEN_LENGTH
        ]
        if invalid_tokens:
            raise ValidationError(
                {
                    "allowed_symbols": (
                        "Cada símbolo debe contener uno o dos caracteres "
                        "alfanuméricos, sin espacios ni separadores."
                    )
                }
            )

        if len(tokens) > MAX_PRODUCT_SYMBOLS:
            raise ValidationError(
                {
                    "allowed_symbols": (
                        f"El universo admite como máximo {MAX_PRODUCT_SYMBOLS} símbolos."
                    )
                }
            )

        if len(set(tokens)) != len(tokens):
            raise ValidationError(
                {
                    "allowed_symbols": (
                        "Los símbolos permitidos no pueden repetirse."
                    )
                }
            )

        if len(tokens) < 2:
            raise ValidationError(
                {
                    "allowed_symbols": (
                        "Un producto personalizado requiere al menos dos "
                        "símbolos disponibles."
                    )
                }
            )

        if self.selection_count is None:
            return

        if not 2 <= self.selection_count <= 8:
            raise ValidationError(
                {
                    "selection_count": (
                        "La cantidad de posiciones debe estar entre 2 y 8."
                    )
                }
            )

        if self.selection_count > len(tokens):
            raise ValidationError(
                {
                    "selection_count": (
                        "La cantidad no puede superar el número de símbolos "
                        "disponibles."
                    )
                }
            )

    @classmethod
    def rule_for_code(cls, code: str) -> dict[str, object]:
        try:
            return cls.PRODUCT_RULES[code]
        except KeyError as exc:
            raise ValidationError(
                {"code": "El tipo de producto oficial no es válido."}
            ) from exc

    def save(self, *args, **kwargs) -> None:
        self.kind = (self.kind or "").strip().upper()
        self.code = (self.code or "").strip().upper()
        if self.kind == self.Kind.CUSTOM:
            self.allowed_symbols = _serialize_symbol_tokens(self.symbol_tokens)
        else:
            self.allowed_symbols = (self.allowed_symbols or "").strip().upper()
        self._validate_persisted_immutability()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class DrawEventQuerySet(models.QuerySet):
    """Bloquea actualizaciones masivas de la configuración crítica."""

    PROTECTED_FIELDS = {
        "product",
        "product_id",
        "sales_open_at",
        "sales_close_at",
        "draw_at",
        "price_minor",
        "prize_minor",
        "status",
        "cancellation_reason",
    }

    def update(self, **kwargs):
        if self.PROTECTED_FIELDS.intersection(kwargs):
            raise ValidationError(
                "La configuración crítica del evento no se actualiza "
                "mediante QuerySet.update()."
            )
        return super().update(**kwargs)


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

    IMMUTABLE_AFTER_DRAFT_FIELDS = (
        "product_id",
        "sales_open_at",
        "draw_at",
        "price_minor",
        "prize_minor",
    )

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

    objects = DrawEventQuerySet.as_manager()

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

    def _persisted_original(self):
        if not self.pk:
            return None
        return (
            type(self).objects
            .filter(pk=self.pk)
            .only(
                "status",
                "product",
                "sales_open_at",
                "draw_at",
                "price_minor",
                "prize_minor",
            )
            .first()
        )

    def _validate_persisted_immutability(self) -> None:
        original = self._persisted_original()
        if original is None or original.status == self.Status.DRAFT:
            return

        changed_fields = [
            field_name
            for field_name in self.IMMUTABLE_AFTER_DRAFT_FIELDS
            if getattr(self, field_name) != getattr(original, field_name)
        ]
        if changed_fields:
            labels = ", ".join(changed_fields)
            raise ValidationError(
                "Un evento publicado o posterior no permite cambiar: "
                f"{labels}."
            )

        if self.status != original.status:
            raise ValidationError(
                {
                    "status": (
                        "El estado de un evento que dejó Borrador solo "
                        "puede cambiar mediante una acción específica."
                    )
                }
            )

    def clean(self) -> None:
        super().clean()
        self._validate_persisted_immutability()

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
        self._validate_persisted_immutability()

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



class DrawEventStatusTransition(models.Model):
    """Historial inmutable de cambios progresivos de estado del evento."""

    id = models.BigAutoField(primary_key=True)
    event = models.ForeignKey(
        "lottery.DrawEvent",
        on_delete=models.PROTECT,
        related_name="status_transitions",
        verbose_name="evento",
    )
    from_status = models.CharField(
        "estado anterior",
        max_length=30,
        choices=DrawEvent.Status.choices,
    )
    to_status = models.CharField(
        "estado nuevo",
        max_length=30,
        choices=DrawEvent.Status.choices,
    )
    reason = models.TextField("motivo administrativo")
    public_message = models.TextField("mensaje público", blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="lottery_status_transitions",
        null=True,
        blank=True,
        verbose_name="cambiado por",
    )
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(
                fields=("event", "created_at"),
                name="lot_status_event_date_idx",
            ),
        ]
        verbose_name = "transición de estado"
        verbose_name_plural = "transiciones de estado"

    def clean(self):
        super().clean()
        if not (self.reason or "").strip():
            raise ValidationError({"reason": "La transición requiere un motivo."})

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("El historial de estados es inmutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("El historial de estados no se elimina.")

    def __str__(self):
        return f"{self.event}: {self.from_status} → {self.to_status}"


def _raw_selection_tokens(*, value, product: LotteryProduct) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(_normalize_symbol_token(token) for token in value)

    raw = _normalize_symbol_token(value)
    if not raw:
        return ()

    if SYMBOL_TOKEN_SEPARATOR in raw:
        return tuple(
            _normalize_symbol_token(token)
            for token in raw.split(SYMBOL_TOKEN_SEPARATOR)
        )

    if "," in raw:
        return tuple(
            _normalize_symbol_token(token)
            for token in raw.split(",")
        )

    allowed_tokens = product.symbol_tokens
    if allowed_tokens and all(len(token) == 1 for token in allowed_tokens):
        return tuple(raw)

    return (raw,)


def _serialize_lottery_key(tokens: tuple[str, ...]) -> str:
    if all(len(token) == 1 for token in tokens):
        return "".join(tokens)
    return SYMBOL_TOKEN_SEPARATOR.join(tokens)


def split_lottery_key(*, value: str, product: LotteryProduct) -> tuple[str, ...]:
    """Separa una clave persistida para presentarla como celdas."""
    raw = _normalize_symbol_token(value)
    if not raw:
        return ()
    if SYMBOL_TOKEN_SEPARATOR in raw:
        return tuple(raw.split(SYMBOL_TOKEN_SEPARATOR))
    if all(len(token) == 1 for token in product.symbol_tokens):
        return tuple(raw)
    return (raw,)


def normalize_lottery_key(value, product: LotteryProduct | None = None) -> str:
    """Normaliza una selección; con producto también aplica orden canónico."""
    if product is None:
        return _normalize_symbol_token(value)
    return validate_key_for_product(value=value, product=product)


def validate_key_for_product(
    *,
    value,
    product: LotteryProduct,
    field_name: str | None = None,
) -> str:
    """Valida tokens, evita repetición y devuelve la clave canónica.

    Los errores son ValidationError simples. El formulario o modelo consumidor
    decide a qué campo asociarlos; así no se produce TypeError al limpiar un
    campo individual de Django.
    """
    tokens = _raw_selection_tokens(value=value, product=product)

    if len(tokens) != product.selection_count:
        raise ValidationError(
            f"La combinación debe contener exactamente "
            f"{product.selection_count} símbolos.",
            code="invalid_selection_length",
        )

    allowed_tokens = product.symbol_tokens
    allowed_set = set(allowed_tokens)
    invalid_tokens = sorted(set(tokens) - allowed_set)
    if invalid_tokens:
        raise ValidationError(
            "La combinación contiene símbolos no permitidos: "
            f"{', '.join(invalid_tokens)}.",
            code="invalid_selection_symbol",
        )

    if len(set(tokens)) != len(tokens):
        raise ValidationError(
            "Los símbolos de la combinación deben ser únicos.",
            code="repeated_selection_symbol",
        )

    order = {token: index for index, token in enumerate(allowed_tokens)}
    canonical_tokens = tuple(sorted(tokens, key=order.__getitem__))
    return _serialize_lottery_key(canonical_tokens)


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
        max_length=64,
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
    award_operation_id = models.UUIDField(
        "operación de premio",
        blank=True,
        null=True,
        unique=True,
        editable=False,
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

        try:
            self.normalized_key = validate_key_for_product(
                value=self.normalized_key,
                product=self.event.product,
            )
        except ValidationError as exc:
            raise ValidationError(
                {"normalized_key": exc.messages}
            ) from exc

        if self.price_minor != self.event.price_minor:
            raise ValidationError(
                {
                    "price_minor": (
                        "El precio histórico del boleto debe coincidir con "
                        "el precio fijo del evento al crearlo."
                    )
                }
            )

    @property
    def key_tokens(self) -> tuple[str, ...]:
        if not self.event_id:
            return ()
        return split_lottery_key(
            value=self.normalized_key,
            product=self.event.product,
        )

    @property
    def key_display(self) -> str:
        return " · ".join(self.key_tokens)

    def save(self, *args, **kwargs) -> None:
        if self.event_id:
            self.normalized_key = validate_key_for_product(
                value=self.normalized_key,
                product=self.event.product,
            )
        else:
            self.normalized_key = normalize_lottery_key(self.normalized_key)
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
        max_length=64,
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

        try:
            self.winning_key = validate_key_for_product(
                value=self.winning_key,
                product=self.event.product,
            )
        except ValidationError as exc:
            raise ValidationError(
                {"winning_key": exc.messages}
            ) from exc

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

    @property
    def key_tokens(self) -> tuple[str, ...]:
        if not self.event_id:
            return ()
        return split_lottery_key(
            value=self.winning_key,
            product=self.event.product,
        )

    @property
    def key_display(self) -> str:
        return " · ".join(self.key_tokens)

    def save(self, *args, **kwargs) -> None:
        if self.pk is not None:
            raise ValidationError(
                "El resultado publicado es inmutable."
            )

        if self.event_id:
            self.winning_key = validate_key_for_product(
                value=self.winning_key,
                product=self.event.product,
            )
        else:
            self.winning_key = normalize_lottery_key(self.winning_key)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Los resultados publicados son históricos y no se eliminan."
        )

    def __str__(self) -> str:
        return f"{self.event.name}: {self.winning_key}"
