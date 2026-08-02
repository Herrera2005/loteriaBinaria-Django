"""Servicios transaccionales del módulo vendors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.roles import CLIENT, VENDOR
from apps.finance.models import Movement, Wallet
from django.db.models.deletion import ProtectedError

from .models import ConversionAssignment, ConversionRequest, VendorProfile


@dataclass(frozen=True)
class VendorProfileRemovalResult:
    """Resultado de eliminar físicamente o desactivar un perfil."""

    profile_id: int
    username: str
    physically_deleted: bool
    deactivated: bool


def vendor_profile_has_history(profile: VendorProfile) -> bool:
    """Devuelve True cuando el perfil conserva relaciones históricas.

    La inspección usa las relaciones declaradas por Django. Actualmente cubre
    asignaciones y, cuando se agreguen compras u otras relaciones protegidas
    hacia VendorProfile, también quedarán detectadas sin depender de SQL
    exclusivo de una base concreta.
    """
    for relation in profile._meta.related_objects:
        if relation.many_to_many:
            continue

        accessor_name = relation.get_accessor_name()

        if relation.one_to_one:
            try:
                getattr(profile, accessor_name)
            except relation.related_model.DoesNotExist:
                continue
            return True

        related_manager = getattr(profile, accessor_name, None)
        if related_manager is not None and related_manager.exists():
            return True

    return False


@transaction.atomic
def remove_or_deactivate_vendor_profile(
    *,
    profile_id: int,
) -> VendorProfileRemovalResult:
    """Elimina solo perfiles sin historia; en otro caso los desactiva."""
    profile = (
        VendorProfile.objects
        .select_for_update()
        .select_related("user")
        .get(pk=profile_id)
    )
    username = profile.user.username

    if vendor_profile_has_history(profile):
        if profile.status != VendorProfile.Status.DISABLED:
            profile.status = VendorProfile.Status.DISABLED
            profile.save(update_fields=("status", "updated_at"))

        return VendorProfileRemovalResult(
            profile_id=profile_id,
            username=username,
            physically_deleted=False,
            deactivated=True,
        )

    try:
        profile.delete()
    except ProtectedError:
        profile.status = VendorProfile.Status.DISABLED
        profile.save(update_fields=("status", "updated_at"))
        return VendorProfileRemovalResult(
            profile_id=profile_id,
            username=username,
            physically_deleted=False,
            deactivated=True,
        )

    return VendorProfileRemovalResult(
        profile_id=profile_id,
        username=username,
        physically_deleted=True,
        deactivated=False,
    )


CONVERSION_REQUEST_LIFETIME_MINUTES = 5


def _assert_active_client(user) -> None:
    if (
        not user.is_active
        or user.status != User.Status.ACTIVE
        or not user.groups.filter(name=CLIENT).exists()
    ):
        raise ValidationError("Se requiere una cuenta CLIENTE activa.")


def _positive_amount(amount_minor: int) -> int:
    amount = int(amount_minor)
    if amount <= 0:
        raise ValidationError("El monto debe ser mayor que cero.")
    return amount


@transaction.atomic
def create_conversion_request(
    *,
    client,
    amount_minor: int,
    operation_id,
) -> tuple[ConversionRequest, bool]:
    """Reserva REAL y crea una solicitud idempotente para vendedores."""

    _assert_active_client(client)
    amount = _positive_amount(amount_minor)

    existing = ConversionRequest.objects.filter(
        operation_id=operation_id,
    ).first()
    if existing is not None:
        if existing.client_id != client.pk or existing.amount_minor != amount:
            raise ValidationError(
                "El identificador de operación ya fue utilizado con otros datos."
            )
        return existing, False

    try:
        real_wallet = (
            Wallet.objects
            .select_for_update()
            .get(user=client, currency=Wallet.Currency.REAL)
        )
    except Wallet.DoesNotExist as exc:
        raise ValidationError("La wallet REAL requerida no existe.") from exc

    if real_wallet.status != Wallet.Status.ACTIVE:
        raise ValidationError("La wallet REAL no está activa.")
    if real_wallet.available_minor < amount:
        raise ValidationError("Saldo REAL insuficiente.")

    real_wallet.available_minor -= amount
    real_wallet.reserved_minor += amount
    real_wallet.save(
        update_fields=(
            "available_minor",
            "reserved_minor",
            "updated_at",
        )
    )

    conversion_request = ConversionRequest.objects.create(
        client=client,
        operation_id=operation_id,
        amount_minor=amount,
        status=ConversionRequest.Status.PENDING,
        expires_at=(
            timezone.now()
            + timedelta(minutes=CONVERSION_REQUEST_LIFETIME_MINUTES)
        ),
    )

    Movement.objects.create(
        wallet=real_wallet,
        operation_id=operation_id,
        type=Movement.Type.CONVERSION_REQUEST,
        direction=Movement.Direction.DEBIT,
        amount_minor=amount,
        balance_after_minor=real_wallet.available_minor,
        description=(
            "Reserva REAL para solicitud de conversión REAL a VIRTUAL."
        ),
    )

    return conversion_request, True


def _active_vendor_profile(vendor) -> VendorProfile:
    if (
        not vendor.is_active
        or vendor.status != User.Status.ACTIVE
        or not vendor.groups.filter(name=VENDOR).exists()
    ):
        raise ValidationError("Se requiere una cuenta VENDEDOR activa.")

    try:
        profile = VendorProfile.objects.select_related("user").get(user=vendor)
    except VendorProfile.DoesNotExist as exc:
        raise ValidationError(
            "La cuenta no tiene un perfil vendedor registrado."
        ) from exc

    if profile.status != VendorProfile.Status.ACTIVE:
        raise ValidationError("El perfil vendedor no está activo.")

    return profile


def eligible_conversion_requests(*, vendor):
    """Solicitudes que el vendedor puede cubrir en este instante.

    La consulta no cambia estados ni saldos. El servicio de asignación vuelve
    a validar todas las condiciones bajo bloqueo transaccional.
    """

    _active_vendor_profile(vendor)

    try:
        virtual_wallet = Wallet.objects.get(
            user=vendor,
            currency=Wallet.Currency.VIRTUAL,
        )
    except Wallet.DoesNotExist:
        return ConversionRequest.objects.none()

    if virtual_wallet.status != Wallet.Status.ACTIVE:
        return ConversionRequest.objects.none()

    return (
        ConversionRequest.objects
        .filter(
            status=ConversionRequest.Status.PENDING,
            expires_at__gt=timezone.now(),
            amount_minor__lte=virtual_wallet.available_minor,
        )
        .exclude(client_id=vendor.pk)
        .exclude(assignments__status=ConversionAssignment.Status.ACTIVE)
        .select_related("client")
        .distinct()
        .order_by("expires_at", "created_at", "id")
    )


@transaction.atomic
def assign_conversion_request(
    *,
    vendor,
    request_id: int,
) -> ConversionAssignment:
    """Asigna una solicitud y reserva el VIRTUAL que deberá entregarse.

    La solicitud conserva su vencimiento original. La primera asignación
    válida cambia la solicitud a IN_PROGRESS; las siguientes fallan.
    """

    profile = _active_vendor_profile(vendor)
    now = timezone.now()

    try:
        conversion_request = (
            ConversionRequest.objects
            .select_for_update()
            .select_related("client")
            .get(pk=request_id)
        )
    except ConversionRequest.DoesNotExist as exc:
        raise ValidationError("La solicitud no existe.") from exc

    if conversion_request.client_id == vendor.pk:
        raise ValidationError(
            "No puedes atender una solicitud creada por tu misma cuenta."
        )
    if conversion_request.status != ConversionRequest.Status.PENDING:
        raise ValidationError("La solicitud ya no está disponible.")
    if conversion_request.expires_at <= now:
        raise ValidationError("La solicitud ya venció.")
    if ConversionAssignment.objects.filter(
        request=conversion_request,
        status=ConversionAssignment.Status.ACTIVE,
    ).exists():
        raise ValidationError("La solicitud ya fue tomada por otro vendedor.")

    try:
        virtual_wallet = (
            Wallet.objects
            .select_for_update()
            .get(user=vendor, currency=Wallet.Currency.VIRTUAL)
        )
    except Wallet.DoesNotExist as exc:
        raise ValidationError("La wallet VIRTUAL requerida no existe.") from exc

    if virtual_wallet.status != Wallet.Status.ACTIVE:
        raise ValidationError("La wallet VIRTUAL no está activa.")
    if virtual_wallet.available_minor < conversion_request.amount_minor:
        raise ValidationError("Inventario VIRTUAL insuficiente.")

    virtual_wallet.available_minor -= conversion_request.amount_minor
    virtual_wallet.reserved_minor += conversion_request.amount_minor
    virtual_wallet.save(
        update_fields=(
            "available_minor",
            "reserved_minor",
            "updated_at",
        )
    )

    conversion_request.status = ConversionRequest.Status.IN_PROGRESS
    conversion_request.save(update_fields=("status", "updated_at"))

    return ConversionAssignment.objects.create(
        request=conversion_request,
        vendor=profile,
        status=ConversionAssignment.Status.ACTIVE,
    )

@transaction.atomic
def complete_conversion_request(
    *,
    vendor,
    assignment_id: int,
) -> tuple[ConversionAssignment, bool]:
    """Liquida una solicitud asignada en una sola transacción.

    Efectos finales:
    - consume REAL reservado del Cliente y lo acredita al Vendedor;
    - consume VIRTUAL reservado del Vendedor y lo acredita al Cliente;
    - completa solicitud y asignación;
    - registra movimientos correlacionados con ``request.operation_id``.

    Devuelve ``(assignment, completed_now)``. Una repetición exacta sobre una
    asignación ya completada es idempotente y devuelve ``False``.
    """

    profile = _active_vendor_profile(vendor)
    now = timezone.now()

    try:
        assignment = (
            ConversionAssignment.objects
            .select_for_update()
            .select_related("request", "request__client", "vendor")
            .get(pk=assignment_id)
        )
    except ConversionAssignment.DoesNotExist as exc:
        raise ValidationError("La asignación no existe.") from exc

    if assignment.vendor_id != profile.pk:
        raise ValidationError("La asignación no pertenece a este vendedor.")

    conversion_request = (
        ConversionRequest.objects
        .select_for_update()
        .select_related("client")
        .get(pk=assignment.request_id)
    )

    if (
        assignment.status == ConversionAssignment.Status.COMPLETED
        and conversion_request.status
        == ConversionRequest.Status.COMPLETED_BY_VENDOR
    ):
        return assignment, False

    if assignment.status != ConversionAssignment.Status.ACTIVE:
        raise ValidationError("La asignación ya no está activa.")
    if conversion_request.status != ConversionRequest.Status.IN_PROGRESS:
        raise ValidationError("La solicitud ya no está en proceso.")
    if conversion_request.expires_at <= now:
        raise ValidationError(
            "La solicitud venció y ya no puede completarse por el vendedor."
        )

    amount = conversion_request.amount_minor
    wallet_keys = {
        (conversion_request.client_id, Wallet.Currency.REAL),
        (conversion_request.client_id, Wallet.Currency.VIRTUAL),
        (vendor.pk, Wallet.Currency.REAL),
        (vendor.pk, Wallet.Currency.VIRTUAL),
    }
    locked_wallets = {
        (wallet.user_id, wallet.currency): wallet
        for wallet in (
            Wallet.objects
            .select_for_update()
            .filter(
                user_id__in={key[0] for key in wallet_keys},
                currency__in=(Wallet.Currency.REAL, Wallet.Currency.VIRTUAL),
            )
            .order_by("user_id", "currency")
        )
    }

    missing = wallet_keys.difference(locked_wallets)
    if missing:
        raise ValidationError("Falta una wallet requerida para completar la solicitud.")

    client_real = locked_wallets[(conversion_request.client_id, Wallet.Currency.REAL)]
    client_virtual = locked_wallets[(conversion_request.client_id, Wallet.Currency.VIRTUAL)]
    vendor_real = locked_wallets[(vendor.pk, Wallet.Currency.REAL)]
    vendor_virtual = locked_wallets[(vendor.pk, Wallet.Currency.VIRTUAL)]

    for wallet in (client_real, client_virtual, vendor_real, vendor_virtual):
        if wallet.status != Wallet.Status.ACTIVE:
            raise ValidationError("Todas las wallets involucradas deben estar activas.")

    if client_real.reserved_minor < amount:
        raise ValidationError("El REAL reservado del cliente es insuficiente.")
    if vendor_virtual.reserved_minor < amount:
        raise ValidationError("El VIRTUAL reservado del vendedor es insuficiente.")

    client_real.reserved_minor -= amount
    vendor_virtual.reserved_minor -= amount
    client_virtual.available_minor += amount
    vendor_real.available_minor += amount

    for wallet, fields in (
        (client_real, ("reserved_minor", "updated_at")),
        (vendor_virtual, ("reserved_minor", "updated_at")),
        (client_virtual, ("available_minor", "updated_at")),
        (vendor_real, ("available_minor", "updated_at")),
    ):
        wallet.save(update_fields=fields)

    operation_id = conversion_request.operation_id
    Movement.objects.bulk_create(
        [
            Movement(
                wallet=vendor_virtual,
                operation_id=operation_id,
                type=Movement.Type.CONVERSION_REQUEST,
                direction=Movement.Direction.DEBIT,
                amount_minor=amount,
                balance_after_minor=vendor_virtual.available_minor,
                description=(
                    "Entrega VIRTUAL al cliente por solicitud completada."
                ),
            ),
            Movement(
                wallet=client_virtual,
                operation_id=operation_id,
                type=Movement.Type.CONVERSION_REQUEST,
                direction=Movement.Direction.CREDIT,
                amount_minor=amount,
                balance_after_minor=client_virtual.available_minor,
                description=(
                    "Recepción VIRTUAL por solicitud completada por vendedor."
                ),
            ),
            Movement(
                wallet=vendor_real,
                operation_id=operation_id,
                type=Movement.Type.CONVERSION_REQUEST,
                direction=Movement.Direction.CREDIT,
                amount_minor=amount,
                balance_after_minor=vendor_real.available_minor,
                description=(
                    "Recepción REAL por solicitud completada al cliente."
                ),
            ),
        ]
    )

    conversion_request.status = ConversionRequest.Status.COMPLETED_BY_VENDOR
    conversion_request.completed_at = now
    conversion_request.save(
        update_fields=("status", "completed_at", "updated_at")
    )

    assignment.status = ConversionAssignment.Status.COMPLETED
    assignment.completed_at = now
    assignment.save(update_fields=("status", "completed_at"))

    return assignment, True

