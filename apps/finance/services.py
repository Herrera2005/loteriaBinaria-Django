"""Servicios atómicos e idempotentes de Finance."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from apps.accounts.models import User
from apps.accounts.roles import CLIENT, VENDOR

from .models import (
    Movement,
    TopUp,
    VendorInventoryPurchase,
    VirtualToRealConversion,
    VirtualTransfer,
    Wallet,
    Withdrawal,
)


UserModel = get_user_model()
ACTIVE_USER_STATUS = "ACTIVE"


def _initial_wallet_status(user):
    if user.is_active and getattr(user, "status", None) == ACTIVE_USER_STATUS:
        return Wallet.Status.ACTIVE
    return Wallet.Status.SUSPENDED


@transaction.atomic
def ensure_user_wallets(user):
    if user is None or not getattr(user, "pk", None):
        raise ValidationError(
            "El usuario debe estar guardado antes de crear sus wallets."
        )

    result = {}
    for currency in (Wallet.Currency.REAL, Wallet.Currency.VIRTUAL):
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            currency=currency,
            defaults={"status": _initial_wallet_status(user)},
        )
        result[currency] = wallet
    return result


def _assert_role(user, role_code: str, message: str) -> None:
    if (
        not user.is_active
        or user.status != User.Status.ACTIVE
        or not user.groups.filter(name=role_code).exists()
    ):
        raise ValidationError(message)


def _assert_client(user) -> None:
    _assert_role(user, CLIENT, "Se requiere una cuenta CLIENTE activa.")


def _assert_vendor(user) -> None:
    _assert_role(user, VENDOR, "Se requiere una cuenta VENDEDOR activa.")

    from apps.vendors.models import VendorProfile

    profile = VendorProfile.objects.filter(user=user).first()
    if profile is None or profile.status != VendorProfile.Status.ACTIVE:
        raise ValidationError(
            "Se requiere un perfil vendedor activo para operar."
        )


def _wallet(user, currency):
    try:
        wallet = Wallet.objects.select_for_update().get(
            user=user,
            currency=currency,
        )
    except Wallet.DoesNotExist as exc:
        raise ValidationError("La wallet requerida no existe.") from exc

    if wallet.status != Wallet.Status.ACTIVE:
        raise ValidationError("La wallet no está activa.")
    return wallet


def _positive(amount):
    amount = int(amount)
    if amount <= 0:
        raise ValidationError("El monto debe ser mayor que cero.")
    return amount


def _movement(wallet, operation_id, movement_type, direction, amount, description):
    return Movement.objects.create(
        wallet=wallet,
        operation_id=operation_id,
        type=movement_type,
        direction=direction,
        amount_minor=amount,
        balance_after_minor=wallet.available_minor,
        description=description,
    )


def _confirm_topup_for_role(*, user, amount_minor, operation_id, role_code):
    if role_code == CLIENT:
        _assert_client(user)
    elif role_code == VENDOR:
        _assert_vendor(user)
    else:
        raise ValidationError("Rol financiero no permitido.")

    amount = _positive(amount_minor)
    existing = TopUp.objects.filter(operation_id=operation_id).first()
    if existing:
        if existing.user_id != user.pk or existing.amount_minor != amount:
            raise ValidationError(
                "El identificador de operación ya fue utilizado con otros datos."
            )
        return existing, False

    wallet = _wallet(user, Wallet.Currency.REAL)
    wallet.available_minor += amount
    wallet.save(update_fields=("available_minor", "updated_at"))

    obj = TopUp.objects.create(
        user=user,
        amount_minor=amount,
        operation_id=operation_id,
    )
    _movement(
        wallet,
        operation_id,
        Movement.Type.TOP_UP,
        Movement.Direction.CREDIT,
        amount,
        "Recarga REAL académica 1:1.",
    )
    return obj, True


@transaction.atomic
def confirm_topup(*, user, amount_minor, operation_id):
    return _confirm_topup_for_role(
        user=user,
        amount_minor=amount_minor,
        operation_id=operation_id,
        role_code=CLIENT,
    )


@transaction.atomic
def confirm_vendor_topup(*, user, amount_minor, operation_id):
    return _confirm_topup_for_role(
        user=user,
        amount_minor=amount_minor,
        operation_id=operation_id,
        role_code=VENDOR,
    )


def _convert_virtual_to_real_for_role(
    *, user, gross_virtual_minor, operation_id, role_code
):
    if role_code == CLIENT:
        _assert_client(user)
    elif role_code == VENDOR:
        _assert_vendor(user)
    else:
        raise ValidationError("Rol financiero no permitido.")

    gross = _positive(gross_virtual_minor)
    existing = VirtualToRealConversion.objects.filter(
        operation_id=operation_id
    ).first()
    if existing:
        if existing.user_id != user.pk or existing.amount_minor != gross:
            raise ValidationError(
                "El identificador de operación ya fue utilizado con otros datos."
            )
        return existing, False

    fee = (gross * 10) // 100
    net = gross - fee
    if fee <= 0 or net <= 0:
        raise ValidationError(
            "El monto es demasiado pequeño para aplicar la conversión 90/10."
        )

    virtual_wallet = _wallet(user, Wallet.Currency.VIRTUAL)
    real_wallet = _wallet(user, Wallet.Currency.REAL)
    if virtual_wallet.available_minor < gross:
        raise ValidationError("Saldo VIRTUAL insuficiente.")

    virtual_wallet.available_minor -= gross
    real_wallet.available_minor += net
    virtual_wallet.save(update_fields=("available_minor", "updated_at"))
    real_wallet.save(update_fields=("available_minor", "updated_at"))

    obj = VirtualToRealConversion.objects.create(
        user=user,
        amount_minor=gross,
        fee_virtual_minor=fee,
        net_real_minor=net,
        operation_id=operation_id,
    )
    _movement(
        virtual_wallet,
        operation_id,
        Movement.Type.VIRTUAL_TO_REAL,
        Movement.Direction.DEBIT,
        gross,
        "Débito bruto de conversión VIRTUAL a REAL.",
    )
    _movement(
        real_wallet,
        operation_id,
        Movement.Type.VIRTUAL_TO_REAL,
        Movement.Direction.CREDIT,
        net,
        "Crédito REAL neto después de comisión del 10 %.",
    )
    return obj, True


@transaction.atomic
def convert_virtual_to_real(*, user, gross_virtual_minor, operation_id):
    return _convert_virtual_to_real_for_role(
        user=user,
        gross_virtual_minor=gross_virtual_minor,
        operation_id=operation_id,
        role_code=CLIENT,
    )


@transaction.atomic
def convert_vendor_virtual_to_real(
    *, user, gross_virtual_minor, operation_id
):
    return _convert_virtual_to_real_for_role(
        user=user,
        gross_virtual_minor=gross_virtual_minor,
        operation_id=operation_id,
        role_code=VENDOR,
    )


@transaction.atomic
def transfer_virtual(
    *, sender, recipient_identifier, amount_minor, operation_id
):
    _assert_client(sender)
    amount = _positive(amount_minor)
    existing = VirtualTransfer.objects.filter(operation_id=operation_id).first()
    if existing:
        if existing.user_id != sender.pk or existing.amount_minor != amount:
            raise ValidationError(
                "El identificador de operación ya fue utilizado con otros datos."
            )
        return existing, False

    identifier = recipient_identifier.strip()
    recipient = (
        UserModel.objects
        .filter(
            Q(username__iexact=identifier)
            | Q(email__iexact=identifier)
        )
        .distinct()
        .first()
    )
    if recipient is None:
        raise ValidationError(
            "No existe un cliente con ese usuario o correo."
        )
    _assert_client(recipient)
    if recipient.pk == sender.pk:
        raise ValidationError(
            "No puedes transferirte VIRTUAL a ti mismo."
        )

    user_ids = sorted((sender.pk, recipient.pk))
    wallets = list(
        Wallet.objects
        .select_for_update()
        .filter(
            user_id__in=user_ids,
            currency=Wallet.Currency.VIRTUAL,
        )
        .order_by("user_id")
    )
    by_user = {wallet.user_id: wallet for wallet in wallets}
    source = by_user.get(sender.pk)
    target = by_user.get(recipient.pk)
    if not source or not target:
        raise ValidationError("Una de las wallets VIRTUAL no existe.")
    if (
        source.status != Wallet.Status.ACTIVE
        or target.status != Wallet.Status.ACTIVE
    ):
        raise ValidationError(
            "Ambas wallets VIRTUAL deben estar activas."
        )
    if source.available_minor < amount:
        raise ValidationError("Saldo VIRTUAL insuficiente.")

    source.available_minor -= amount
    target.available_minor += amount
    source.save(update_fields=("available_minor", "updated_at"))
    target.save(update_fields=("available_minor", "updated_at"))

    obj = VirtualTransfer.objects.create(
        user=sender,
        recipient=recipient,
        amount_minor=amount,
        operation_id=operation_id,
    )
    _movement(
        source,
        operation_id,
        Movement.Type.VIRTUAL_TRANSFER,
        Movement.Direction.DEBIT,
        amount,
        f"Transferencia VIRTUAL enviada a {recipient.username}.",
    )
    _movement(
        target,
        operation_id,
        Movement.Type.VIRTUAL_TRANSFER,
        Movement.Direction.CREDIT,
        amount,
        f"Transferencia VIRTUAL recibida de {sender.username}.",
    )
    return obj, True


def _confirm_withdrawal_for_role(
    *, user, amount_minor, operation_id, role_code
):
    if role_code == CLIENT:
        _assert_client(user)
    elif role_code == VENDOR:
        _assert_vendor(user)
    else:
        raise ValidationError("Rol financiero no permitido.")

    amount = _positive(amount_minor)
    existing = Withdrawal.objects.filter(operation_id=operation_id).first()
    if existing:
        if existing.user_id != user.pk or existing.amount_minor != amount:
            raise ValidationError(
                "El identificador de operación ya fue utilizado con otros datos."
            )
        return existing, False

    wallet = _wallet(user, Wallet.Currency.REAL)
    if wallet.available_minor < amount:
        raise ValidationError("Saldo REAL insuficiente.")

    wallet.available_minor -= amount
    wallet.save(update_fields=("available_minor", "updated_at"))
    obj = Withdrawal.objects.create(
        user=user,
        amount_minor=amount,
        operation_id=operation_id,
    )
    _movement(
        wallet,
        operation_id,
        Movement.Type.WITHDRAWAL,
        Movement.Direction.DEBIT,
        amount,
        "Retiro académico sin comisión adicional.",
    )
    return obj, True


@transaction.atomic
def confirm_withdrawal(*, user, amount_minor, operation_id):
    return _confirm_withdrawal_for_role(
        user=user,
        amount_minor=amount_minor,
        operation_id=operation_id,
        role_code=CLIENT,
    )


@transaction.atomic
def confirm_vendor_withdrawal(*, user, amount_minor, operation_id):
    return _confirm_withdrawal_for_role(
        user=user,
        amount_minor=amount_minor,
        operation_id=operation_id,
        role_code=VENDOR,
    )


@transaction.atomic
def purchase_vendor_inventory(
    *, vendor, virtual_minor, operation_id
):
    """Compra VIRTUAL a razón exacta de $0.90 por V1.00."""

    _assert_vendor(vendor)
    virtual_amount = _positive(virtual_minor)
    if virtual_amount % 100 != 0:
        raise ValidationError(
            "La compra mayorista debe usar unidades VIRTUAL completas."
        )

    real_cost = (virtual_amount * 90) // 100
    existing = VendorInventoryPurchase.objects.filter(
        operation_id=operation_id
    ).first()
    if existing:
        if (
            existing.user_id != vendor.pk
            or existing.amount_minor != virtual_amount
            or existing.cost_real_minor != real_cost
        ):
            raise ValidationError(
                "El identificador de operación ya fue utilizado con otros datos."
            )
        return existing, False

    real_wallet = _wallet(vendor, Wallet.Currency.REAL)
    existing = VendorInventoryPurchase.objects.filter(
        operation_id=operation_id
    ).first()

    if existing:
        if (
            existing.user_id != vendor.pk
            or existing.amount_minor != virtual_amount
            or existing.cost_real_minor != real_cost
        ):
            raise ValidationError(
                "El identificador de operación "
                "ya fue utilizado con otros datos."
            )

        return existing, False
    virtual_wallet = _wallet(vendor, Wallet.Currency.VIRTUAL)
    if real_wallet.available_minor < real_cost:
        raise ValidationError(
            "Saldo REAL insuficiente para la compra mayorista."
        )

    real_wallet.available_minor -= real_cost
    virtual_wallet.available_minor += virtual_amount
    real_wallet.save(update_fields=("available_minor", "updated_at"))
    virtual_wallet.save(update_fields=("available_minor", "updated_at"))

    purchase = VendorInventoryPurchase.objects.create(
        user=vendor,
        amount_minor=virtual_amount,
        cost_real_minor=real_cost,
        operation_id=operation_id,
    )
    _movement(
        real_wallet,
        operation_id,
        Movement.Type.WHOLESALE_PURCHASE,
        Movement.Direction.DEBIT,
        real_cost,
        "Costo REAL de compra mayorista VIRTUAL a razón 0.90 por 1.00.",
    )
    _movement(
        virtual_wallet,
        operation_id,
        Movement.Type.WHOLESALE_PURCHASE,
        Movement.Direction.CREDIT,
        virtual_amount,
        "Inventario VIRTUAL acreditado por compra mayorista.",
    )
    return purchase, True
