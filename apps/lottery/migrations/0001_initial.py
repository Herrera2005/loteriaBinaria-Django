# Generated for Taller #3; portable between SQLite and MySQL.

import django.core.validators
import django.db.models.deletion
import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LotteryProduct",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        choices=[
                            ("OCTAL", "Octal"),
                            ("DECIMAL", "Decimal"),
                            ("HEXADECIMAL", "Hexadecimal"),
                        ],
                        max_length=20,
                        unique=True,
                        verbose_name="código",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=80,
                        verbose_name="nombre",
                    ),
                ),
                (
                    "allowed_symbols",
                    models.CharField(
                        max_length=32,
                        verbose_name="símbolos permitidos",
                    ),
                ),
                (
                    "selection_count",
                    models.PositiveSmallIntegerField(
                        verbose_name="cantidad de símbolos",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        verbose_name="activo",
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
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="actualizado",
                    ),
                ),
            ],
            options={
                "verbose_name": "producto de lotería",
                "verbose_name_plural": "productos de lotería",
                "ordering": ("id",),
            },
        ),
        migrations.CreateModel(
            name="DrawEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=150,
                        verbose_name="nombre",
                    ),
                ),
                (
                    "sales_open_at",
                    models.DateTimeField(
                        verbose_name="apertura de ventas",
                    ),
                ),
                (
                    "sales_close_at",
                    models.DateTimeField(
                        editable=False,
                        verbose_name="cierre de ventas",
                    ),
                ),
                (
                    "draw_at",
                    models.DateTimeField(
                        verbose_name="fecha del sorteo",
                    ),
                ),
                (
                    "price_minor",
                    models.BigIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1)
                        ],
                        verbose_name="precio en unidades menores",
                    ),
                ),
                (
                    "prize_minor",
                    models.BigIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1)
                        ],
                        verbose_name=(
                            "premio fijo en unidades menores"
                        ),
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("DRAFT", "Borrador"),
                            ("SCHEDULED", "Programado"),
                            ("PUBLISHED", "Publicado"),
                            ("SALES_OPEN", "Ventas abiertas"),
                            ("SALES_CLOSED", "Ventas cerradas"),
                            ("RESULT_SET", "Resultado fijado"),
                            ("FINISHED", "Finalizado"),
                            ("CANCELLED", "Cancelado"),
                        ],
                        db_index=True,
                        default="DRAFT",
                        max_length=30,
                        verbose_name="estado",
                    ),
                ),
                (
                    "cancellation_reason",
                    models.TextField(
                        blank=True,
                        verbose_name="motivo de cancelación",
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
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="actualizado",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="events",
                        to="lottery.lotteryproduct",
                        verbose_name="producto",
                    ),
                ),
            ],
            options={
                "verbose_name": "evento de sorteo",
                "verbose_name_plural": "eventos de sorteo",
                "ordering": ("draw_at", "id"),
            },
        ),
        migrations.CreateModel(
            name="DrawResult",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "winning_key",
                    models.CharField(
                        max_length=16,
                        verbose_name="combinación ganadora",
                    ),
                ),
                (
                    "reason",
                    models.TextField(verbose_name="motivo"),
                ),
                (
                    "published_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="publicado",
                    ),
                ),
                (
                    "event",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="result",
                        to="lottery.drawevent",
                        verbose_name="evento",
                    ),
                ),
                (
                    "published_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="published_draw_results",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="publicado por",
                    ),
                ),
            ],
            options={
                "verbose_name": "resultado de sorteo",
                "verbose_name_plural": "resultados de sorteo",
                "ordering": ("-published_at", "-id"),
            },
        ),
        migrations.CreateModel(
            name="Ticket",
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
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="identificador de operación",
                    ),
                ),
                (
                    "normalized_key",
                    models.CharField(
                        max_length=16,
                        verbose_name="combinación normalizada",
                    ),
                ),
                (
                    "price_minor",
                    models.BigIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1)
                        ],
                        verbose_name="precio en unidades menores",
                    ),
                ),
                (
                    "ownership_status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Activo"),
                            ("REFUNDED", "Reembolsado"),
                            ("CANCELLED", "Cancelado"),
                        ],
                        db_index=True,
                        default="ACTIVE",
                        max_length=20,
                        verbose_name="estado de propiedad",
                    ),
                ),
                (
                    "evaluation_status",
                    models.CharField(
                        choices=[
                            (
                                "PENDING_RESULT",
                                "Pendiente de resultado",
                            ),
                            ("NOT_WINNER", "No ganador"),
                            ("REFUND", "Reembolso"),
                            ("WINNER", "Ganador"),
                        ],
                        db_index=True,
                        default="PENDING_RESULT",
                        max_length=30,
                        verbose_name="estado de evaluación",
                    ),
                ),
                (
                    "award_minor",
                    models.BigIntegerField(
                        default=0,
                        validators=[
                            django.core.validators.MinValueValidator(0)
                        ],
                        verbose_name=(
                            "premio acreditado en unidades menores"
                        ),
                    ),
                ),
                (
                    "credited_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="acreditado",
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
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="tickets",
                        to="lottery.drawevent",
                        verbose_name="evento",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="tickets",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="cliente",
                    ),
                ),
            ],
            options={
                "verbose_name": "boleto",
                "verbose_name_plural": "boletos",
                "ordering": ("-created_at", "-id"),
            },
        ),
        migrations.AddConstraint(
            model_name="lotteryproduct",
            constraint=models.CheckConstraint(
                condition=models.Q(("selection_count__gt", 0)),
                name="lot_prod_selection_gt_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="lotteryproduct",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        ("allowed_symbols", "01234567"),
                        ("code", "OCTAL"),
                        ("selection_count", 4),
                    )
                    | models.Q(
                        ("allowed_symbols", "0123456789"),
                        ("code", "DECIMAL"),
                        ("selection_count", 5),
                    )
                    | models.Q(
                        (
                            "allowed_symbols",
                            "0123456789ABCDEF",
                        ),
                        ("code", "HEXADECIMAL"),
                        ("selection_count", 6),
                    )
                ),
                name="lot_prod_valid_config",
            ),
        ),
        migrations.AddIndex(
            model_name="drawevent",
            index=models.Index(
                fields=["product", "status"],
                name="lot_event_prod_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="drawevent",
            index=models.Index(
                fields=["draw_at"],
                name="lot_event_draw_at_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="drawevent",
            constraint=models.CheckConstraint(
                condition=models.Q(("price_minor__gt", 0)),
                name="lot_event_price_gt_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="drawevent",
            constraint=models.CheckConstraint(
                condition=models.Q(("prize_minor__gt", 0)),
                name="lot_event_prize_gt_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="drawevent",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("sales_open_at__lt", models.F("sales_close_at"))
                ),
                name="lot_event_open_before_close",
            ),
        ),
        migrations.AddConstraint(
            model_name="drawevent",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("sales_close_at__lt", models.F("draw_at"))
                ),
                name="lot_event_close_before_draw",
            ),
        ),
        migrations.AddIndex(
            model_name="drawresult",
            index=models.Index(
                fields=["published_at"],
                name="lot_result_published_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="ticket",
            index=models.Index(
                fields=["user", "created_at"],
                name="lot_ticket_user_date_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="ticket",
            index=models.Index(
                fields=["event", "evaluation_status"],
                name="lot_ticket_event_eval_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="ticket",
            constraint=models.UniqueConstraint(
                fields=("event", "normalized_key"),
                name="lot_ticket_event_key_uq",
            ),
        ),
        migrations.AddConstraint(
            model_name="ticket",
            constraint=models.CheckConstraint(
                condition=models.Q(("price_minor__gt", 0)),
                name="lot_ticket_price_gt_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="ticket",
            constraint=models.CheckConstraint(
                condition=models.Q(("award_minor__gte", 0)),
                name="lot_ticket_award_gte_0",
            ),
        ),
    ]
