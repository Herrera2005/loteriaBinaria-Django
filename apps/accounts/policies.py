"""Políticas de roles y modo activo para el Taller #3."""

from __future__ import annotations

from typing import Any

from .models import User
from .roles import ADMINISTRATOR, CLIENT, ROLE_CODES, VENDOR


ACTIVE_MODE_SESSION_KEY = "active_mode"


def assigned_role_codes(user) -> tuple[str, ...]:
    """Devuelve Groups válidos en el orden canónico del taller."""
    if not getattr(user, "is_authenticated", False):
        return ()

    assigned = set(
        user.groups.filter(name__in=ROLE_CODES).values_list(
            "name",
            flat=True,
        )
    )
    return tuple(code for code in ROLE_CODES if code in assigned)


def is_operational_user(user) -> bool:
    """Comprueba autenticación y estado operativo de la cuenta."""
    return bool(
        getattr(user, "is_authenticated", False)
        and user.is_active
        and user.status == User.Status.ACTIVE
    )


def has_assigned_role(user, role_code: str) -> bool:
    if role_code not in ROLE_CODES:
        return False
    return role_code in assigned_role_codes(user)


def get_active_mode(request) -> str | None:
    """Obtiene y sanea session['active_mode'] desde el backend."""
    if not is_operational_user(request.user):
        request.session.pop(ACTIVE_MODE_SESSION_KEY, None)
        return None

    active_mode = request.session.get(ACTIVE_MODE_SESSION_KEY)
    if has_assigned_role(request.user, active_mode):
        return active_mode

    request.session.pop(ACTIVE_MODE_SESSION_KEY, None)
    return None


def can_operate_in_mode(request, expected_mode: str) -> bool:
    """Exige cuenta activa, Group asignado y modo coincidente."""
    return bool(
        expected_mode in ROLE_CODES
        and is_operational_user(request.user)
        and has_assigned_role(request.user, expected_mode)
        and get_active_mode(request) == expected_mode
    )


def can_use_client_functions(request) -> bool:
    return can_operate_in_mode(request, CLIENT)


def can_use_vendor_functions(request) -> bool:
    return can_operate_in_mode(request, VENDOR)


def can_use_administrator_functions(request) -> bool:
    return bool(
        can_operate_in_mode(request, ADMINISTRATOR)
        and request.user.is_staff
    )


def can_purchase_ticket(request) -> bool:
    """Solo el modo CLIENTE habilita compra, incluso en multirrol."""
    return can_use_client_functions(request)


def can_administer_event(request, event: Any) -> bool:
    """Impide administrar un evento en el que el usuario tiene boleto."""
    if not can_use_administrator_functions(request):
        return False

    return not event.tickets.filter(user=request.user).exists()
