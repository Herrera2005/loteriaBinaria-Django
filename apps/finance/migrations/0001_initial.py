# Generated for Taller #3 — portable between SQLite and MySQL.

import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_existing_user_wallets(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Wallet = apps.get_model("finance", "Wallet")
    database_alias = schema_editor.connection.alias

    for user in User.objects.using(database_alias).order_by("pk").iterator():
        initial_status = (
            "ACTIVE"
            if user.is_active and user.status == "ACTIVE"
            else "SUSPENDED"
        )
        for currency in ("REAL", "VIRTUAL"):
            Wallet.objects.using(database_alias).get_or_create(
                user_id=user.pk,
                currency=currency,
                defaults={
                    "available_minor": 0,
                    "reserved_minor": 0,
                    "status": initial_status,
                },
            )


def preserve_wallets_on_reverse(apps, schema_editor):
    """La reversión de esquema elimina la tabla; no hay borrado manual."""


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Wallet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        choices=[
                            ("REAL", "REAL"),
                            ("VIRTUAL", "VIRTUAL"),
                        ],
                        max_length=10,
                        verbose_name="moneda",
                    ),
                ),
                (
                    "available_minor",
                    models.BigIntegerField(
                        default=0,
                        validators=[
                            django.core.validators.MinValueValidator(0)
                        ],
                        verbose_name=(
                            "saldo disponible en unidades menores"
                        ),
                    ),
                ),
                (
                    "reserved_minor",
                    models.BigIntegerField(
                        default=0,
                        validators=[
                            django.core.validators.MinValueValidator(0)
                        ],
                        verbose_name=(
                            "saldo reservado en unidades menores"
                        ),
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Activa"),
                            ("SUSPENDED", "Suspendida"),
                            ("BLOCKED", "Bloqueada"),
                            ("DISABLED", "Desactivada"),
                        ],
                        db_index=True,
                        default="ACTIVE",
                        max_length=20,
                        verbose_name="estado",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="creada",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="actualizada",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="wallets",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="usuario",
                    ),
                ),
            ],
            options={
                "verbose_name": "wallet",
                "verbose_name_plural": "wallets",
                "ordering": ("user__username", "currency"),
                "indexes": [
                    models.Index(
                        fields=["user", "status"],
                        name="fin_wallet_user_status_idx",
                    ),
                    models.Index(
                        fields=["currency", "status"],
                        name="fin_wallet_curr_status_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("user", "currency"),
                        name="fin_wallet_user_curr_uq",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("available_minor__gte", 0)
                        ),
                        name="fin_wallet_available_gte_0",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("reserved_minor__gte", 0)
                        ),
                        name="fin_wallet_reserved_gte_0",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Movement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "operation_id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        verbose_name="identificador de operación",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("TOP_UP", "Recarga REAL simulada"),
                            (
                                "VIRTUAL_TO_REAL",
                                "Conversión VIRTUAL a REAL",
                            ),
                            (
                                "VIRTUAL_TRANSFER",
                                "Transferencia VIRTUAL",
                            ),
                            (
                                "WHOLESALE_PURCHASE",
                                "Compra mayorista",
                            ),
                            (
                                "CONVERSION_REQUEST",
                                "Solicitud de conversión",
                            ),
                            (
                                "TICKET_PURCHASE",
                                "Compra de boleto",
                            ),
                            ("PRIZE", "Premio"),
                            ("REFUND", "Reembolso"),
                            ("WITHDRAWAL", "Retiro simulado"),
                            (
                                "ADJUSTMENT",
                                "Ajuste administrativo",
                            ),
                        ],
                        db_index=True,
                        max_length=40,
                        verbose_name="tipo",
                    ),
                ),
                (
                    "direction",
                    models.CharField(
                        choices=[
                            ("CREDIT", "Crédito"),
                            ("DEBIT", "Débito"),
                        ],
                        max_length=10,
                        verbose_name="dirección",
                    ),
                ),
                (
                    "amount_minor",
                    models.BigIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1)
                        ],
                        verbose_name="monto en unidades menores",
                    ),
                ),
                (
                    "balance_after_minor",
                    models.BigIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0)
                        ],
                        verbose_name=(
                            "saldo posterior en unidades menores"
                        ),
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="descripción",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="creado",
                    ),
                ),
                (
                    "wallet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="movements",
                        to="finance.wallet",
                        verbose_name="wallet",
                    ),
                ),
            ],
            options={
                "verbose_name": "movimiento",
                "verbose_name_plural": "movimientos",
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(
                        fields=["wallet", "created_at"],
                        name="fin_move_wallet_date_idx",
                    ),
                    models.Index(
                        fields=["type", "created_at"],
                        name="fin_move_type_date_idx",
                    ),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("amount_minor__gt", 0)),
                        name="fin_move_amount_gt_0",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("balance_after_minor__gte", 0)
                        ),
                        name="fin_move_balance_gte_0",
                    ),
                ],
            },
        ),
        migrations.RunPython(
            backfill_existing_user_wallets,
            preserve_wallets_on_reverse,
        ),
    ]
