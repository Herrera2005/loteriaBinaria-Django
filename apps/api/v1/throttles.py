from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS
from rest_framework.settings import api_settings
from rest_framework.throttling import (
    AnonRateThrottle,
    ScopedRateThrottle,
)


class LoginRateThrottle(AnonRateThrottle):
    """
    Limita los intentos anónimos de inicio de sesión.
    """

    scope = "login"


class UnsafeMethodScopedRateThrottle(
    ScopedRateThrottle
):
    """
    Aplica throttling por scope únicamente a métodos
    que modifican estado.

    GET, HEAD y OPTIONS no consumen este límite adicional.

    La tasa se obtiene desde la configuración vigente de DRF
    para respetar también override_settings durante las pruebas.
    """

    def allow_request(
        self,
        request,
        view,
    ):
        if request.method in SAFE_METHODS:
            return True

        return super().allow_request(
            request,
            view,
        )

    def get_rate(self):
        if not self.scope:
            return None

        return api_settings.DEFAULT_THROTTLE_RATES.get(
            self.scope
        )