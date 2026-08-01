"""Autorización por rol asignado y modo activo de sesión."""

from __future__ import annotations

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .models import User
from .roles import ROLE_CODES


ACTIVE_MODE_SESSION_KEY = "active_mode"


def assigned_mode_codes(user) -> tuple[str, ...]:
    """Devuelve roles asignados en el orden canónico del Taller #3."""
    if not user.is_authenticated:
        return ()
    names = set(user.groups.filter(name__in=ROLE_CODES).values_list("name", flat=True))
    return tuple(code for code in ROLE_CODES if code in names)


def get_valid_active_mode(request) -> str | None:
    """Obtiene el modo solo si continúa asignado al usuario."""
    active_mode = request.session.get(ACTIVE_MODE_SESSION_KEY)
    if active_mode in assigned_mode_codes(request.user):
        return active_mode
    request.session.pop(ACTIVE_MODE_SESSION_KEY, None)
    return None


def active_mode_required(expected_mode: str):
    """Protege una vista contra mezcla de permisos o manipulación de URL."""
    if expected_mode not in ROLE_CODES:
        raise ValueError(f"Modo no reconocido: {expected_mode}")

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_active or user.status != User.Status.ACTIVE:
                raise PermissionDenied("La cuenta no está activa para operar.")

            active_mode = get_valid_active_mode(request)
            if active_mode is None:
                return redirect("accounts:choose_mode")
            if active_mode != expected_mode:
                raise PermissionDenied(
                    "La ruta no corresponde al modo activo de la sesión."
                )
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
