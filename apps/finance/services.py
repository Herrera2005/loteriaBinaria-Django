"""Servicios mínimos y transaccionales de Finance para P-28A."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Wallet


ACTIVE_USER_STATUS = "ACTIVE"


def _initial_wallet_status(user) -> str:
    if user.is_active and getattr(user, "status", None) == ACTIVE_USER_STATUS:
        return Wallet.Status.ACTIVE
    return Wallet.Status.SUSPENDED


@transaction.atomic
def ensure_user_wallets(user) -> dict[str, Wallet]:
    """Garantiza una wallet REAL y una VIRTUAL sin modificar saldos.

    Es idempotente y puede invocarse desde creación de usuarios, asignación de
    roles, seeds o comandos de backfill. Nunca debe ejecutarse desde una vista
    GET como efecto secundario.
    """

    if user is None or not getattr(user, "pk", None):
        raise ValidationError(
            "El usuario debe estar guardado antes de crear sus wallets."
        )

    initial_status = _initial_wallet_status(user)
    wallets: dict[str, Wallet] = {}

    for currency in (
        Wallet.Currency.REAL,
        Wallet.Currency.VIRTUAL,
    ):
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            currency=currency,
            defaults={
                "available_minor": 0,
                "reserved_minor": 0,
                "status": initial_status,
            },
        )
        wallets[currency] = wallet

    return wallets
