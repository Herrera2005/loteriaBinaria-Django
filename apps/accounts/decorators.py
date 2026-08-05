"""Decoradores de acceso basados en políticas de servidor."""

from __future__ import annotations

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .policies import can_operate_in_mode, get_active_mode
from .roles import ROLE_CODES


def active_mode_required(expected_mode: str):
    """Protege vistas funcionales según Group y active_mode."""
    if expected_mode not in ROLE_CODES:
        raise ValueError(f"Modo no reconocido: {expected_mode}")

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if get_active_mode(request) is None:
                return redirect("accounts:choose_mode")

            if not can_operate_in_mode(request, expected_mode):
                raise PermissionDenied(
                    "La ruta no corresponde al modo activo de la sesión."
                )

            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
