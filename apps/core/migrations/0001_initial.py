# Generated for Taller #3 — portable between SQLite and MySQL.

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
            name="AuditEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "active_mode",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("CLIENTE", "Cliente"),
                            ("VENDEDOR", "Vendedor"),
                            ("ADMINISTRADOR", "Administrador"),
                        ],
                        default="",
                        max_length=20,
                        verbose_name="modo activo",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        db_index=True,
                        max_length=100,
                        verbose_name="acción",
                    ),
                ),
                (
                    "resource_type",
                    models.CharField(
                        max_length=100,
                        verbose_name="tipo de recurso",
                    ),
                ),
                (
                    "resource_id",
                    models.CharField(
                        max_length=100,
                        verbose_name="identificador del recurso",
                    ),
                ),
                (
                    "reason",
                    models.TextField(
                        blank=True,
                        verbose_name="motivo",
                    ),
                ),
                (
                    "metadata",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text=(
                            "Texto complementario de auditoría. No es "
                            "fuente de verdad y no debe contener "
                            "contraseñas, tokens ni secretos."
                        ),
                        verbose_name="metadata no sensible",
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        blank=True,
                        null=True,
                        verbose_name="dirección IP aproximada",
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
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="audit_events",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="actor",
                    ),
                ),
            ],
            options={
                "verbose_name": "evento de auditoría",
                "verbose_name_plural": "eventos de auditoría",
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(
                        fields=["actor", "created_at"],
                        name="core_audit_actor_date_idx",
                    ),
                    models.Index(
                        fields=["action", "created_at"],
                        name="core_audit_action_date_idx",
                    ),
                    models.Index(
                        fields=["resource_type", "resource_id"],
                        name="core_audit_resource_idx",
                    ),
                ],
            },
        ),
    ]
