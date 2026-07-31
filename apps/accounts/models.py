from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    """Usuario personalizado definitivo del Taller #3."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activo"
        SUSPENDED = "SUSPENDED", "Suspendido"
        BLOCKED = "BLOCKED", "Bloqueado"
        DISABLED = "DISABLED", "Desactivado"

    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(
        "correo electrónico",
        unique=True,
    )
    document = models.CharField(
        "documento",
        max_length=30,
        unique=True,
    )
    phone = models.CharField(
        "teléfono",
        max_length=30,
        blank=True,
    )
    birth_date = models.DateField(
        "fecha de nacimiento",
    )
    status = models.CharField(
        "estado",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(
        "creado",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "actualizado",
        auto_now=True,
    )

    REQUIRED_FIELDS = ["email", "document", "birth_date"]

    class Meta:
        ordering = ("username",)
        indexes = [
            models.Index(
                fields=("email",),
                name="accounts_user_email_idx",
            ),
            models.Index(
                fields=("document",),
                name="accounts_user_doc_idx",
            ),
            models.Index(
                fields=("status",),
                name="accounts_user_status_idx",
            ),
        ]
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def clean(self) -> None:
        super().clean()

        self.email = self.normalize_email_value(self.email)
        self.document = self.document.strip()
        self.phone = self.phone.strip()

        if not self.document:
            raise ValidationError(
                {"document": "El documento no puede quedar vacío."}
            )

    def save(self, *args, **kwargs) -> None:
        # Se normaliza también aquí para cubrir createsuperuser, admin y ORM.
        # Las validaciones de edad y reglas de registro irán en forms/services.
        self.email = self.normalize_email_value(self.email)
        self.document = self.document.strip()
        self.phone = self.phone.strip()
        super().save(*args, **kwargs)

    @staticmethod
    def normalize_email_value(email: str | None) -> str:
        return (email or "").strip().lower()

    def __str__(self) -> str:
        return f"{self.username} ({self.email})"


class TermsVersion(models.Model):
    """Versión inmutable de términos o política de privacidad."""

    class Kind(models.TextChoices):
        TERMS = "TERMS", "Términos y condiciones"
        PRIVACY = "PRIVACY", "Política de privacidad"

    id = models.BigAutoField(primary_key=True)
    kind = models.CharField(
        "tipo",
        max_length=20,
        choices=Kind.choices,
    )
    version = models.CharField(
        "versión",
        max_length=30,
    )
    title = models.CharField(
        "título",
        max_length=150,
    )
    content = models.TextField(
        "contenido",
    )
    effective_at = models.DateTimeField(
        "vigente desde",
    )
    is_active = models.BooleanField(
        "activa",
        default=True,
    )
    created_at = models.DateTimeField(
        "creada",
        auto_now_add=True,
    )

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
        verbose_name="usuario",
    )
    terms_version = models.ForeignKey(
        "accounts.TermsVersion",
        on_delete=models.PROTECT,
        related_name="acceptances",
        verbose_name="versión de términos",
    )
    accepted_at = models.DateTimeField(
        "aceptada",
        auto_now_add=True,
    )
    ip_address = models.GenericIPAddressField(
        "dirección IP",
        blank=True,
        null=True,
    )

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
