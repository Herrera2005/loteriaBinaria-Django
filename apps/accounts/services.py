"""Servicios transaccionales del módulo accounts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from .models import TermsAcceptance, TermsVersion, User
from .roles import CLIENT


MINIMUM_AGE = 18


@dataclass(frozen=True)
class RegistrationData:
    username: str
    email: str
    document: str
    phone: str
    birth_date: date
    first_name: str
    last_name: str
    password: str


def age_cutoff(today: date | None = None) -> date:
    """Fecha máxima de nacimiento permitida para alcanzar 18 años."""
    current = today or timezone.localdate()
    try:
        return current.replace(year=current.year - MINIMUM_AGE)
    except ValueError:
        return current.replace(year=current.year - MINIMUM_AGE, month=2, day=28)


def current_terms_version(kind: str) -> TermsVersion | None:
    """Última versión activa y vigente del tipo indicado."""
    return (
        TermsVersion.objects.filter(
            kind=kind,
            is_active=True,
            effective_at__lte=timezone.now(),
        )
        .order_by("-effective_at", "-created_at")
        .first()
    )


def _locked_current_version(
    *,
    submitted: TermsVersion,
    expected_kind: str,
) -> TermsVersion:
    now = timezone.now()
    submitted_locked = TermsVersion.objects.select_for_update().get(
        pk=submitted.pk
    )
    latest_locked = (
        TermsVersion.objects.select_for_update()
        .filter(
            kind=expected_kind,
            is_active=True,
            effective_at__lte=now,
        )
        .order_by("-effective_at", "-created_at")
        .first()
    )
    if (
        submitted_locked.kind != expected_kind
        or not submitted_locked.is_active
        or submitted_locked.effective_at > now
        or latest_locked is None
        or latest_locked.pk != submitted_locked.pk
    ):
        raise ValidationError(
            "La versión legal seleccionada dejó de ser la vigente."
        )
    return submitted_locked


@transaction.atomic
def register_client(
    *,
    data: RegistrationData,
    terms_version: TermsVersion,
    privacy_version: TermsVersion,
    ip_address: str | None,
) -> User:
    """Crea un cliente y registra dos aceptaciones en una sola transacción."""
    locked_terms = _locked_current_version(
        submitted=terms_version,
        expected_kind=TermsVersion.Kind.TERMS,
    )
    locked_privacy = _locked_current_version(
        submitted=privacy_version,
        expected_kind=TermsVersion.Kind.PRIVACY,
    )

    if data.birth_date > age_cutoff():
        raise ValidationError("El registro exige ser mayor de edad.")

    username = User.normalize_username_value(data.username)
    email = User.normalize_email_value(data.email)
    document = User.normalize_document_value(data.document)
    duplicate_exists = (
        User.objects.filter(username__iexact=username).exists()
        or User.objects.filter(email__iexact=email).exists()
        or User.objects.filter(document__iexact=document).exists()
    )
    if duplicate_exists:
        raise ValidationError(
            "El usuario, correo o documento ya se encuentra registrado."
        )

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            document=document,
            phone=data.phone.strip(),
            birth_date=data.birth_date,
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            password=data.password,
            status=User.Status.ACTIVE,
            is_active=True,
        )
    except IntegrityError as exc:
        raise ValidationError(
            "El usuario, correo o documento ya se encuentra registrado."
        ) from exc

    client_group, _ = Group.objects.get_or_create(name=CLIENT)
    user.groups.add(client_group)

    TermsAcceptance.objects.create(
        user=user,
        terms_version=locked_terms,
        ip_address=ip_address,
    )
    TermsAcceptance.objects.create(
        user=user,
        terms_version=locked_privacy,
        ip_address=ip_address,
    )
    return user


@dataclass(frozen=True)
class UserRemovalResult:
    """Resultado estable de la baja física o desactivación lógica."""

    action: str
    username: str


def user_has_related_history(user: User) -> bool:
    """Detecta relaciones históricas reales sin depender de apps concretas."""
    for relation in user._meta.related_objects:
        if relation.many_to_many:
            continue

        accessor_name = relation.get_accessor_name()

        if relation.one_to_one:
            try:
                getattr(user, accessor_name)
            except relation.related_model.DoesNotExist:
                continue
            return True

        related_manager = getattr(user, accessor_name, None)
        if related_manager is not None and related_manager.exists():
            return True

    return False


def _deactivate_user(user: User) -> None:
    user.status = User.Status.DISABLED
    user.is_active = False
    user.save(update_fields=("status", "is_active", "updated_at"))


@transaction.atomic
def delete_or_deactivate_user(
    *,
    actor: User,
    target_id: int,
) -> UserRemovalResult:
    """Elimina solo sin historia; de lo contrario desactiva preservando historial."""
    target = User.objects.select_for_update().get(pk=target_id)

    if target.pk == actor.pk:
        raise ValidationError(
            "No puedes eliminar ni desactivar tu propia cuenta desde esta operación."
        )

    if target.is_superuser:
        raise ValidationError(
            "Los superusuarios no se eliminan ni desactivan desde este CRUD."
        )

    username = target.username

    if user_has_related_history(target):
        _deactivate_user(target)
        return UserRemovalResult(action="deactivated", username=username)

    try:
        target.delete()
    except ProtectedError:
        # Una relación protegida pudo aparecer después de la comprobación inicial.
        target = User.objects.select_for_update().get(pk=target_id)
        _deactivate_user(target)
        return UserRemovalResult(action="deactivated", username=username)

    return UserRemovalResult(action="deleted", username=username)
