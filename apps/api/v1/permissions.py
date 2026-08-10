from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.accounts.policies import is_operational_user

from .modes import (
    ACTIVE_MODE_HEADER,
    normalize_active_mode,
    user_can_operate_as,
)


class IsOperationalUser(BasePermission):
    message = (
        "La cuenta no se encuentra habilitada "
        "para operar."
    )

    def has_permission(self, request, view):
        return is_operational_user(
            request.user
        )


class HasActiveMode(BasePermission):
    message = (
        "Debe indicar un modo activo válido."
    )

    def has_permission(self, request, view):
        requested_mode = normalize_active_mode(
            request.headers.get(
                ACTIVE_MODE_HEADER
            )
        )

        if requested_mode is None:
            self.message = (
                "Debe indicar el encabezado "
                "X-Active-Mode."
            )
            return False

        if not user_can_operate_as(
            request.user,
            requested_mode,
        ):
            self.message = (
                "El usuario no tiene permiso "
                "para operar con el modo solicitado."
            )
            return False

        request.active_mode = requested_mode

        return True