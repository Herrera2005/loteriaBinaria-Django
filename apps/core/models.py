"""Modelos transversales de auditoría del Taller #3."""

from __future__ import annotations

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.roles import ADMINISTRATOR, CLIENT, VENDOR


class HistoricalAuditQuerySet(models.QuerySet):
    """Bloquea edición y eliminación masivas de auditoría."""

    def update(self, **kwargs):
        raise ValidationError("Los eventos de auditoría no se editan.")

    def delete(self):
        raise ValidationError("Los eventos de auditoría no se eliminan.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("Los eventos de auditoría no se editan.")


class AuditEvent(models.Model):
    """Registro mínimo, append-only y sin secretos de una acción crítica."""

    class ActiveMode(models.TextChoices):
        CLIENT = CLIENT, "Cliente"
        VENDOR = VENDOR, "Vendedor"
        ADMINISTRATOR = ADMINISTRATOR, "Administrador"

    SENSITIVE_METADATA_PATTERN = re.compile(
        r"\b(password|contraseña|token|secret|api[_ -]?key)\b",
        flags=re.IGNORECASE,
    )

    id = models.BigAutoField(primary_key=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_events",
        verbose_name="actor",
    )
    active_mode = models.CharField(
        "modo activo",
        max_length=20,
        choices=ActiveMode.choices,
        blank=True,
        default="",
    )
    action = models.CharField("acción", max_length=100, db_index=True)
    resource_type = models.CharField(
        "tipo de recurso",
        max_length=100,
    )
    resource_id = models.CharField(
        "identificador del recurso",
        max_length=100,
    )
    reason = models.TextField("motivo", blank=True)
    metadata = models.TextField(
        "metadata no sensible",
        blank=True,
        default="",
        help_text=(
            "Texto complementario de auditoría. No es fuente de verdad y no "
            "debe contener contraseñas, tokens ni secretos."
        ),
    )
    ip_address = models.GenericIPAddressField(
        "dirección IP aproximada",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField("creado", auto_now_add=True)

    objects = HistoricalAuditQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(
                fields=("actor", "created_at"),
                name="core_audit_actor_date_idx",
            ),
            models.Index(
                fields=("action", "created_at"),
                name="core_audit_action_date_idx",
            ),
            models.Index(
                fields=("resource_type", "resource_id"),
                name="core_audit_resource_idx",
            ),
        ]
        verbose_name = "evento de auditoría"
        verbose_name_plural = "eventos de auditoría"

    def clean(self) -> None:
        super().clean()

        if self.metadata and self.SENSITIVE_METADATA_PATTERN.search(
            self.metadata
        ):
            raise ValidationError(
                {
                    "metadata": (
                        "La metadata de auditoría no puede contener "
                        "contraseñas, tokens ni secretos."
                    )
                }
            )

    def save(self, *args, **kwargs) -> None:
        if self.pk and type(self)._base_manager.filter(pk=self.pk).exists():
            raise ValidationError("Los eventos de auditoría no se editan.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Los eventos de auditoría no se eliminan.")

    def __str__(self) -> str:
        return f"{self.actor} — {self.action} — {self.resource_type}:{self.resource_id}"
