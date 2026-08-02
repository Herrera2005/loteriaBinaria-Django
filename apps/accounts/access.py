"""Compatibilidad de autorización por rol y modo activo."""

from .decorators import active_mode_required
from .policies import (
    ACTIVE_MODE_SESSION_KEY,
    assigned_role_codes,
    get_active_mode,
)


def assigned_mode_codes(user) -> tuple[str, ...]:
    """Alias conservado para no romper imports existentes."""
    return assigned_role_codes(user)


def get_valid_active_mode(request) -> str | None:
    """Alias conservado para no romper imports existentes."""
    return get_active_mode(request)
