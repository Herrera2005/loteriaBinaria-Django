"""Consultas read-only de wallets y movimientos propios para P-28."""

from __future__ import annotations

from datetime import date
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from apps.accounts.access import get_valid_active_mode
from apps.accounts.models import User
from apps.accounts.roles import DASHBOARD_URL_NAMES

from .models import Movement, Wallet


MOVEMENTS_PER_PAGE = 15


def _operational_mode_required(view_func):
    """Exige cuenta activa y un modo asignado/activo sin fijar un rol único."""

    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_active or user.status != User.Status.ACTIVE:
            raise PermissionDenied("La cuenta no está activa para consultar finanzas.")

        active_mode = get_valid_active_mode(request)
        if active_mode is None:
            return redirect("accounts:choose_mode")

        return view_func(request, *args, **kwargs)

    return wrapped


def _format_minor(amount_minor: int, currency: str, *, signed: bool = False) -> str:
    """Formatea enteros minor sin usar float ni alterar la fuente de verdad."""

    value = int(amount_minor)
    sign = ""
    if signed and value > 0:
        sign = "+"
    elif value < 0:
        sign = "-"

    major, minor = divmod(abs(value), 100)
    prefix = "$" if currency == Wallet.Currency.REAL else "V"
    return f"{sign}{prefix} {major:,}.{minor:02d}"


def _parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _query_without_page(request) -> str:
    query = request.GET.copy()
    query.pop("page", None)
    return query.urlencode()


def _dashboard_url(request) -> str:
    active_mode = get_valid_active_mode(request)
    return reverse(DASHBOARD_URL_NAMES[active_mode])


def _wallet_card(wallet: Wallet) -> dict[str, object]:
    total_minor = wallet.available_minor + wallet.reserved_minor
    return {
        "wallet": wallet,
        "currency": wallet.currency,
        "currency_label": wallet.get_currency_display(),
        "available_display": _format_minor(
            wallet.available_minor,
            wallet.currency,
        ),
        "reserved_display": _format_minor(
            wallet.reserved_minor,
            wallet.currency,
        ),
        "total_display": _format_minor(total_minor, wallet.currency),
        "status": wallet.status,
        "status_label": wallet.get_status_display(),
    }


def _movement_row(movement: Movement) -> dict[str, object]:
    signed_amount = movement.amount_minor
    if movement.direction == Movement.Direction.DEBIT:
        signed_amount *= -1

    return {
        "movement": movement,
        "currency": movement.wallet.currency,
        "currency_label": movement.wallet.get_currency_display(),
        "type_label": movement.get_type_display(),
        "direction": movement.direction,
        "direction_label": movement.get_direction_display(),
        "amount_display": _format_minor(
            signed_amount,
            movement.wallet.currency,
            signed=True,
        ),
        "balance_after_display": _format_minor(
            movement.balance_after_minor,
            movement.wallet.currency,
        ),
    }


@_operational_mode_required
@require_GET
def wallet_detail(request):
    """Muestra únicamente las wallets del usuario autenticado, sin crearlas."""

    wallet_map = {
        wallet.currency: wallet
        for wallet in (
            Wallet.objects
            .filter(user=request.user)
            .order_by("currency")
        )
    }

    wallet_cards = []
    missing_currencies = []
    for currency, label in Wallet.Currency.choices:
        wallet = wallet_map.get(currency)
        if wallet is None:
            missing_currencies.append(label)
            continue
        wallet_cards.append(_wallet_card(wallet))

    return render(
        request,
        "finance/wallet_detail.html",
        {
            "wallet_cards": wallet_cards,
            "missing_currencies": missing_currencies,
            "dashboard_url": _dashboard_url(request),
        },
    )


@_operational_mode_required
@require_GET
def movement_list(request):
    """Lista paginada de movimientos pertenecientes al usuario autenticado."""

    queryset = (
        Movement.objects
        .filter(wallet__user=request.user)
        .select_related("wallet")
        .order_by("-created_at", "-id")
    )

    selected_currency = request.GET.get("currency", "").strip()
    valid_currencies = {value for value, _ in Wallet.Currency.choices}
    if selected_currency in valid_currencies:
        queryset = queryset.filter(wallet__currency=selected_currency)
    else:
        selected_currency = ""

    selected_type = request.GET.get("type", "").strip()
    valid_types = {value for value, _ in Movement.Type.choices}
    if selected_type in valid_types:
        queryset = queryset.filter(type=selected_type)
    else:
        selected_type = ""

    selected_direction = request.GET.get("direction", "").strip()
    valid_directions = {value for value, _ in Movement.Direction.choices}
    if selected_direction in valid_directions:
        queryset = queryset.filter(direction=selected_direction)
    else:
        selected_direction = ""

    date_from_value = request.GET.get("date_from", "").strip()
    date_from = _parse_iso_date(date_from_value)
    if date_from is not None:
        queryset = queryset.filter(created_at__date__gte=date_from)
    else:
        date_from_value = ""

    date_to_value = request.GET.get("date_to", "").strip()
    date_to = _parse_iso_date(date_to_value)
    if date_to is not None:
        queryset = queryset.filter(created_at__date__lte=date_to)
    else:
        date_to_value = ""

    paginator = Paginator(queryset, MOVEMENTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))
    movement_rows = [
        _movement_row(movement)
        for movement in page_obj.object_list
    ]

    return render(
        request,
        "finance/movement_list.html",
        {
            "movement_rows": movement_rows,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "currency_choices": Wallet.Currency.choices,
            "type_choices": Movement.Type.choices,
            "direction_choices": Movement.Direction.choices,
            "selected_currency": selected_currency,
            "selected_type": selected_type,
            "selected_direction": selected_direction,
            "date_from": date_from_value,
            "date_to": date_to_value,
            "query_without_page": _query_without_page(request),
            "dashboard_url": _dashboard_url(request),
        },
    )
