"""Mixins reutilizables para permisos del Taller #3."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .policies import (
    can_administer_event,
    can_operate_in_mode,
    can_use_administrator_functions,
)


class ActiveModeRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Exige un Group asignado y el mismo modo activo."""

    expected_mode: str | None = None
    raise_exception = True

    def test_func(self) -> bool:
        return bool(
            self.expected_mode
            and can_operate_in_mode(
                self.request,
                self.expected_mode,
            )
        )

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )

        raise PermissionDenied(
            "La ruta no corresponde al modo activo de la sesión."
        )


class AdministratorModeRequiredMixin(
    LoginRequiredMixin,
    UserPassesTestMixin,
):
    """Exige Group ADMINISTRADOR, modo ADMINISTRADOR y staff."""

    raise_exception = True

    def test_func(self) -> bool:
        return can_use_administrator_functions(self.request)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )

        raise PermissionDenied(
            "Se requiere una cuenta administrativa activa y el modo "
            "ADMINISTRADOR."
        )


class EventAdministrationRequiredMixin(
    AdministratorModeRequiredMixin,
):
    """Además impide administrar eventos donde el actor tiene boleto."""

    def get_policy_event(self):
        return self.get_object()

    def test_func(self) -> bool:
        if not super().test_func():
            return False

        return can_administer_event(
            self.request,
            self.get_policy_event(),
        )

    def handle_no_permission(self):
        if (
            self.request.user.is_authenticated
            and can_use_administrator_functions(self.request)
        ):
            raise PermissionDenied(
                "No puedes administrar un evento en el que tienes boleto."
            )

        return super().handle_no_permission()