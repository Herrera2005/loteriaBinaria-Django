# Generated for Taller #3 — portable between SQLite and MySQL.

import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ConversionRequest",
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
                    "amount_minor",
                    models.BigIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1)
                        ],
                        verbose_name="monto en unidades menores",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pendiente"),
                            ("IN_PROGRESS", "En proceso"),
                            (
                                "COMPLETED_BY_VENDOR",
                                "Completada por vendedor",
                            ),
                            (
                                "COMPLETED_BY_PLATFORM",
                                "Completada por plataforma",
                            ),
                            ("CANCELLED", "Cancelada"),
                            ("EXPIRED", "Expirada"),
                            (
                                "FAILED_LIQUIDITY",
                                "Fallida por liquidez",
                            ),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=40,
                        verbose_name="estado",
                    ),
                ),
                (
                    "expires_at",
                    models.DateTimeField(verbose_name="vence"),
                ),
                (
                    "completed_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="completada",
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
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="conversion_requests",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="cliente",
                    ),
                ),
            ],
            options={
                "verbose_name": "solicitud de conversión",
                "verbose_name_plural": "solicitudes de conversión",
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(
                        fields=["client", "created_at"],
                        name="vendors_req_client_date_idx",
                    ),
                    models.Index(
                        fields=["status", "expires_at"],
                        name="vendors_req_status_exp_idx",
                    ),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("amount_minor__gt", 0)),
                        name="vendors_request_amount_gt_0",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("expires_at__gt", models.F("created_at"))
                        ),
                        name="vendors_req_exp_after_create",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="VendorProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pendiente"),
                            ("ACTIVE", "Activo"),
                            ("SUSPENDED", "Suspendido"),
                            ("DISABLED", "Desactivado"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=20,
                        verbose_name="estado",
                    ),
                ),
                (
                    "activated_at",
                    models.DateTimeField(
                        blank=True,
                        editable=False,
                        null=True,
                        verbose_name="activado",
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
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="vendor_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="usuario",
                    ),
                ),
            ],
            options={
                "verbose_name": "perfil de vendedor",
                "verbose_name_plural": "perfiles de vendedores",
                "ordering": ("user__username",),
                "indexes": [
                    models.Index(
                        fields=["status", "created_at"],
                        name="vendors_prof_status_date_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="ConversionAssignment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Activa"),
                            ("RELEASED", "Liberada"),
                            ("COMPLETED", "Completada"),
                            ("EXPIRED", "Expirada"),
                        ],
                        db_index=True,
                        default="ACTIVE",
                        max_length=20,
                        verbose_name="estado",
                    ),
                ),
                (
                    "assigned_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="asignada",
                    ),
                ),
                (
                    "released_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="liberada",
                    ),
                ),
                (
                    "completed_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="completada",
                    ),
                ),
                (
                    "request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="assignments",
                        to="vendors.conversionrequest",
                        verbose_name="solicitud",
                    ),
                ),
                (
                    "vendor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="assignments",
                        to="vendors.vendorprofile",
                        verbose_name="vendedor",
                    ),
                ),
            ],
            options={
                "verbose_name": "asignación de conversión",
                "verbose_name_plural": "asignaciones de conversión",
                "ordering": ("-assigned_at", "-id"),
                "indexes": [
                    models.Index(
                        fields=["request", "status"],
                        name="vendors_asg_req_status_idx",
                    ),
                    models.Index(
                        fields=["vendor", "status"],
                        name="vendors_asg_vendor_status_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("request", "vendor", "assigned_at"),
                        name="vendors_asg_req_vend_date_uq",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(("released_at__isnull", True))
                            | models.Q(
                                ("released_at__gte", models.F("assigned_at"))
                            )
                        ),
                        name="vendors_asg_release_after",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(("completed_at__isnull", True))
                            | models.Q(
                                ("completed_at__gte", models.F("assigned_at"))
                            )
                        ),
                        name="vendors_asg_complete_after",
                    ),
                ],
            },
        ),
    ]
