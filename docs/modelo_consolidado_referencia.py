"""
Modelo consolidado de referencia — Taller #3 Lotería Binaria con Django.

IMPORTANTE:
- Este archivo es únicamente documental.
- Debe guardarse en docs/modelo_consolidado_referencia.py.
- No debe añadirse a INSTALLED_APPS ni copiarse completo dentro de una sola app.
- Los modelos se dividirán posteriormente entre accounts, core, finance,
  vendors y lottery.
- No genera datos, señales, formularios, vistas, admin ni migraciones.
- Las reglas críticas deben implementarse después en services.py usando
  transaction.atomic().
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q


# ============================================================================
# APP: accounts
# ============================================================================


class User(AbstractUser):
    """Usuario personalizado definitivo del proyecto."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activo"
        SUSPENDED = "SUSPENDED", "Suspendido"
        BLOCKED = "BLOCKED", "Bloqueado"
        DISABLED = "DISABLED", "Desactivado"

    id = models.BigAutoField(primary_key=True)
    email = models.EmailField("correo electrónico", unique=True)
    document = models.CharField("documento", max_length=30, unique=True)
    phone = models.CharField("teléfono", max_length=30, blank=True)
    birth_date = models.DateField("fecha de nacimiento")
    status = models.CharField(
        "estado",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        ordering = ("username",)
        indexes = [
            models.Index(fields=("email",), name="accounts_user_email_idx"),
            models.Index(fields=("document",), name="accounts_user_doc_idx"),
            models.Index(fields=("status",), name="accounts_user_status_idx"),
        ]
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self) -> str:
        return f"{self.username} ({self.email})"


class TermsVersion(models.Model):
    """Versión inmutable de términos o política de privacidad."""

    class Kind(models.TextChoices):
        TERMS = "TERMS", "Términos y condiciones"
        PRIVACY = "PRIVACY", "Política de privacidad"

    id = models.BigAutoField(primary_key=True)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    version = models.CharField(max_length=30)
    title = models.CharField(max_length=150)
    content = models.TextField()
    effective_at = models.DateTimeField()
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-effective_at", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("kind", "version"),
                name="accounts_terms_kind_version_uq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("kind", "is_active"),
                name="accounts_terms_kind_active_idx",
            ),
            models.Index(
                fields=("effective_at",),
                name="accounts_terms_effective_idx",
            ),
        ]
        verbose_name = "versión de términos"
        verbose_name_plural = "versiones de términos"

    def __str__(self) -> str:
        return f"{self.get_kind_display()} v{self.version}"


class TermsAcceptance(models.Model):
    """Aceptación histórica de una versión concreta de términos."""

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="terms_acceptances",
    )
    terms_version = models.ForeignKey(
        "accounts.TermsVersion",
        on_delete=models.PROTECT,
        related_name="acceptances",
    )
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ("-accepted_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "terms_version"),
                name="accounts_accept_user_terms_uq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("user", "accepted_at"),
                name="accounts_accept_user_date_idx",
            ),
        ]
        verbose_name = "aceptación de términos"
        verbose_name_plural = "aceptaciones de términos"

    def __str__(self) -> str:
        return f"{self.user} aceptó {self.terms_version}"


# ============================================================================
# APP: core
# ============================================================================


class AuditEvent(models.Model):
    """Evento de auditoría append-only."""

    class ActiveMode(models.TextChoices):
        CLIENT = "CLIENTE", "Cliente"
        VENDOR = "VENDEDOR", "Vendedor"
        ADMIN = "ADMINISTRADOR", "Administrador"

    id = models.BigAutoField(primary_key=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_events",
        blank=True,
        null=True,
    )
    active_mode = models.CharField(
        max_length=20,
        choices=ActiveMode.choices,
        blank=True,
    )
    action = models.CharField(max_length=80)
    resource_type = models.CharField(max_length=80)
    resource_id = models.CharField(max_length=64)
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(
                fields=("actor", "created_at"),
                name="core_audit_actor_date_idx",
            ),
            models.Index(
                fields=("resource_type", "resource_id"),
                name="core_audit_resource_idx",
            ),
            models.Index(
                fields=("action", "created_at"),
                name="core_audit_action_date_idx",
            ),
        ]
        verbose_name = "evento de auditoría"
        verbose_name_plural = "eventos de auditoría"

    def __str__(self) -> str:
        return f"{self.action}: {self.resource_type} {self.resource_id}"


# ============================================================================
# APP: finance
# ============================================================================


class Wallet(models.Model):
    """Wallet separada por usuario y moneda."""

    class Currency(models.TextChoices):
        REAL = "REAL", "Real"
        VIRTUAL = "VIRTUAL", "Virtual"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activa"
        BLOCKED = "BLOCKED", "Bloqueada"
        CLOSED = "CLOSED", "Cerrada"

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="wallets",
    )
    currency = models.CharField(max_length=10, choices=Currency.choices)
    available_minor = models.BigIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )
    reserved_minor = models.BigIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("user_id", "currency")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "currency"),
                name="finance_wallet_user_currency_uq",
            ),
            models.CheckConstraint(
                condition=Q(available_minor__gte=0),
                name="finance_wallet_available_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(reserved_minor__gte=0),
                name="finance_wallet_reserved_gte_0",
            ),
        ]
        indexes = [
            models.Index(
                fields=("user", "status"),
                name="finance_wallet_user_status_idx",
            ),
        ]
        verbose_name = "wallet"
        verbose_name_plural = "wallets"

    def __str__(self) -> str:
        return f"{self.user} — {self.get_currency_display()}"


class Movement(models.Model):
    """Movimiento financiero histórico y no editable."""

    class Type(models.TextChoices):
        TOP_UP = "TOP_UP", "Recarga"
        VIRTUAL_TO_REAL = "VIRTUAL_TO_REAL", "Conversión virtual a real"
        TRANSFER = "TRANSFER", "Transferencia"
        VENDOR_PURCHASE = "VENDOR_PURCHASE", "Compra mayorista"
        REQUEST = "REQUEST", "Solicitud"
        TICKET_PURCHASE = "TICKET_PURCHASE", "Compra de boleto"
        PRIZE = "PRIZE", "Premio"
        REFUND = "REFUND", "Reembolso"
        ADJUSTMENT = "ADJUSTMENT", "Ajuste"

    class Direction(models.TextChoices):
        CREDIT = "CREDIT", "Crédito"
        DEBIT = "DEBIT", "Débito"

    id = models.BigAutoField(primary_key=True)
    wallet = models.ForeignKey(
        "finance.Wallet",
        on_delete=models.PROTECT,
        related_name="movements",
    )
    operation_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    type = models.CharField(max_length=30, choices=Type.choices)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    amount_minor = models.BigIntegerField(validators=[MinValueValidator(1)])
    balance_after_minor = models.BigIntegerField(
        validators=[MinValueValidator(0)],
    )
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_minor__gt=0),
                name="finance_move_amount_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(balance_after_minor__gte=0),
                name="finance_move_balance_gte_0",
            ),
        ]
        indexes = [
            models.Index(
                fields=("wallet", "created_at"),
                name="finance_move_wallet_date_idx",
            ),
            models.Index(
                fields=("type", "created_at"),
                name="finance_move_type_date_idx",
            ),
        ]
        verbose_name = "movimiento"
        verbose_name_plural = "movimientos"

    def __str__(self) -> str:
        return (
            f"{self.get_type_display()} "
            f"{self.amount_minor} en {self.wallet}"
        )


# ============================================================================
# APP: vendors
# ============================================================================


class VendorProfile(models.Model):
    """Perfil de vendedor, uno a uno con User."""

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
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    activated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("user__username",)
        indexes = [
            models.Index(
                fields=("status", "created_at"),
                name="vendors_profile_status_date_idx",
            ),
        ]
        verbose_name = "perfil de vendedor"
        verbose_name_plural = "perfiles de vendedores"

    def __str__(self) -> str:
        return f"{self.user} — {self.get_status_display()}"


class ConversionRequest(models.Model):
    """Solicitud histórica de conversión REAL a VIRTUAL."""

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
        FAILED_LIQUIDITY = "FAILED_LIQUIDITY", "Fallida por liquidez"

    id = models.BigAutoField(primary_key=True)
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="conversion_requests",
    )
    operation_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    amount_minor = models.BigIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(
        max_length=40,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_minor__gt=0),
                name="vendors_request_amount_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(expires_at__gt=F("created_at")),
                name="vendors_request_expiry_after_create",
            ),
        ]
        indexes = [
            models.Index(
                fields=("client", "created_at"),
                name="vendors_request_client_date_idx",
            ),
            models.Index(
                fields=("status", "expires_at"),
                name="vendors_request_status_exp_idx",
            ),
        ]
        verbose_name = "solicitud de conversión"
        verbose_name_plural = "solicitudes de conversión"

    def __str__(self) -> str:
        return f"Solicitud {self.operation_id} — {self.get_status_display()}"


class ConversionAssignment(models.Model):
    """Historial de asignación de una solicitud a un vendedor."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activa"
        RELEASED = "RELEASED", "Liberada"
        COMPLETED = "COMPLETED", "Completada"
        EXPIRED = "EXPIRED", "Expirada"

    id = models.BigAutoField(primary_key=True)
    request = models.ForeignKey(
        "vendors.ConversionRequest",
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    vendor = models.ForeignKey(
        "vendors.VendorProfile",
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-assigned_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("request", "vendor", "assigned_at"),
                name="vendors_assign_request_vendor_date_uq",
            ),
            models.CheckConstraint(
                condition=Q(released_at__isnull=True)
                | Q(released_at__gte=F("assigned_at")),
                name="vendors_assign_release_after_assign",
            ),
            models.CheckConstraint(
                condition=Q(completed_at__isnull=True)
                | Q(completed_at__gte=F("assigned_at")),
                name="vendors_assign_complete_after_assign",
            ),
        ]
        indexes = [
            models.Index(
                fields=("request", "status"),
                name="vendors_assign_request_status_idx",
            ),
            models.Index(
                fields=("vendor", "status"),
                name="vendors_assign_vendor_status_idx",
            ),
        ]
        verbose_name = "asignación de conversión"
        verbose_name_plural = "asignaciones de conversión"

    def __str__(self) -> str:
        return (
            f"{self.request.operation_id} → "
            f"{self.vendor.user.username}"
        )


# ============================================================================
# APP: lottery
# ============================================================================


class LotteryProduct(models.Model):
    """Producto oficial: Octal, Decimal o Hexadecimal."""

    class Code(models.TextChoices):
        OCTAL = "OCTAL", "Octal"
        DECIMAL = "DECIMAL", "Decimal"
        HEXADECIMAL = "HEXADECIMAL", "Hexadecimal"

    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=20, choices=Code.choices, unique=True)
    name = models.CharField(max_length=80)
    allowed_symbols = models.CharField(max_length=32)
    selection_count = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("id",)
        constraints = [
            models.CheckConstraint(
                condition=Q(selection_count__gt=0),
                name="lottery_product_selection_gt_0",
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
                name="lottery_product_valid_config",
            ),
        ]
        verbose_name = "producto de lotería"
        verbose_name_plural = "productos de lotería"

    def __str__(self) -> str:
        return self.name


class DrawEvent(models.Model):
    """Evento de sorteo asociado a un producto."""

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
    )
    name = models.CharField(max_length=150)
    sales_open_at = models.DateTimeField()
    sales_close_at = models.DateTimeField()
    draw_at = models.DateTimeField()
    price_minor = models.BigIntegerField(validators=[MinValueValidator(1)])
    prize_minor = models.BigIntegerField(validators=[MinValueValidator(0)])
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("draw_at", "id")
        constraints = [
            models.CheckConstraint(
                condition=Q(price_minor__gt=0),
                name="lottery_event_price_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(prize_minor__gte=0),
                name="lottery_event_prize_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(sales_open_at__lt=F("sales_close_at")),
                name="lottery_event_open_before_close",
            ),
            models.CheckConstraint(
                condition=Q(sales_close_at__lt=F("draw_at")),
                name="lottery_event_close_before_draw",
            ),
        ]
        indexes = [
            models.Index(
                fields=("product", "status"),
                name="lottery_event_product_status_idx",
            ),
            models.Index(
                fields=("draw_at",),
                name="lottery_event_draw_at_idx",
            ),
        ]
        verbose_name = "evento de sorteo"
        verbose_name_plural = "eventos de sorteo"

    def __str__(self) -> str:
        return f"{self.name} — {self.draw_at:%Y-%m-%d %H:%M}"


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
    )
    event = models.ForeignKey(
        "lottery.DrawEvent",
        on_delete=models.PROTECT,
        related_name="tickets",
    )
    operation_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    normalized_key = models.CharField(max_length=16)
    price_minor = models.BigIntegerField(validators=[MinValueValidator(1)])
    ownership_status = models.CharField(
        max_length=20,
        choices=OwnershipStatus.choices,
        default=OwnershipStatus.ACTIVE,
        db_index=True,
    )
    evaluation_status = models.CharField(
        max_length=30,
        choices=EvaluationStatus.choices,
        default=EvaluationStatus.PENDING_RESULT,
        db_index=True,
    )
    award_minor = models.BigIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )
    credited_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("event", "normalized_key"),
                name="lottery_ticket_event_key_uq",
            ),
            models.CheckConstraint(
                condition=Q(price_minor__gt=0),
                name="lottery_ticket_price_gt_0",
            ),
            models.CheckConstraint(
                condition=Q(award_minor__gte=0),
                name="lottery_ticket_award_gte_0",
            ),
        ]
        indexes = [
            models.Index(
                fields=("user", "created_at"),
                name="lottery_ticket_user_date_idx",
            ),
            models.Index(
                fields=("event", "evaluation_status"),
                name="lottery_ticket_event_eval_idx",
            ),
        ]
        verbose_name = "boleto"
        verbose_name_plural = "boletos"

    def __str__(self) -> str:
        return f"{self.normalized_key} — {self.event.name}"


class DrawResult(models.Model):
    """Resultado único e inmutable de un evento."""

    id = models.BigAutoField(primary_key=True)
    event = models.OneToOneField(
        "lottery.DrawEvent",
        on_delete=models.PROTECT,
        related_name="result",
    )
    winning_key = models.CharField(max_length=16)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="published_draw_results",
    )
    reason = models.TextField()
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-published_at", "-id")
        indexes = [
            models.Index(
                fields=("published_at",),
                name="lottery_result_published_idx",
            ),
        ]
        verbose_name = "resultado de sorteo"
        verbose_name_plural = "resultados de sorteo"

    def __str__(self) -> str:
        return f"{self.event.name}: {self.winning_key}"


# ============================================================================
# NOTAS DE DIVISIÓN
# ============================================================================
#
# apps/accounts/models.py
#   - User
#   - TermsVersion
#   - TermsAcceptance
#
# apps/core/models.py
#   - AuditEvent
#
# apps/finance/models.py
#   - Wallet
#   - Movement
#
# apps/vendors/models.py
#   - VendorProfile
#   - ConversionRequest
#   - ConversionAssignment
#
# apps/lottery/models.py
#   - LotteryProduct
#   - DrawEvent
#   - Ticket
#   - DrawResult
#
# Reglas que NO se expresan aquí como constraints por portabilidad:
#   - mayoría de edad;
#   - normalización case-insensitive del email;
#   - cierre exactamente 10 minutos antes del sorteo;
#   - símbolos permitidos y no repetidos en tickets/resultados;
#   - una sola asignación ACTIVE por solicitud;
#   - bloqueo de edición de eventos publicados;
#   - permisos por rol y active_mode;
#   - recarga 1:1;
#   - conversión VIRTUAL -> REAL con 10 %;
#   - compra mayorista 0.90 REAL por 1.00 VIRTUAL;
#   - compra, premio, reembolso y reservas.
#
# Estas reglas deben implementarse más adelante en forms.py, policies.py y,
# especialmente, services.py usando transaction.atomic().
