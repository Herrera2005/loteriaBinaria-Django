from __future__ import annotations

from apps.finance.models import Wallet


REAL = Wallet.Currency.REAL
VIRTUAL = Wallet.Currency.VIRTUAL


def money_data(
    amount_minor: int,
    *,
    currency: str,
) -> dict[str, object]:
    amount_minor = int(
        amount_minor
    )

    if currency == REAL:
        prefix = "$ "
    elif currency == VIRTUAL:
        prefix = "V "
    else:
        raise ValueError(
            f"Moneda API no soportada: {currency}"
        )

    return {
        "minor": amount_minor,
        "currency": currency,
        "display": (
            f"{prefix}"
            f"{amount_minor / 100:,.2f}"
        ),
    }