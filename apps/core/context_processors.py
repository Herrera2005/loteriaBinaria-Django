"""Contexto global de navegación calculado exclusivamente en backend."""

from django.urls import reverse

from apps.accounts.access import get_valid_active_mode
from apps.accounts.roles import (
    ADMINISTRATOR,
    CLIENT,
    DASHBOARD_URL_NAMES,
    ROLE_PRESENTATION,
    VENDOR,
)


MODE_NAVIGATION = {
    CLIENT: (
        ("Panel Cliente", "core:client_dashboard"),
        ("Mis billeteras", "finance:wallet_detail"),
        ("Mis movimientos", "finance:movement_list"),
    ),
    VENDOR: (
        ("Panel Vendedor", "core:vendor_dashboard"),
        ("Mis billeteras", "finance:wallet_detail"),
        ("Mis movimientos", "finance:movement_list"),
    ),
    ADMINISTRATOR: (
        ("Panel Administrador", "core:admin_dashboard"),
        ("Mis billeteras", "finance:wallet_detail"),
        ("Mis movimientos", "finance:movement_list"),
        ("Auditoría", "core:audit_list"),
    ),
}

STAFF_ADMIN_NAVIGATION = (
    ("Usuarios", "accounts:user_list"),
    ("Vendedores", "vendors:vendorprofile_list"),
    ("Solicitudes", "vendors:conversionrequest_list"),
    ("Productos", "lottery:product_list"),
    ("Sorteos", "lottery:event_list"),
)


def _navigation_item(
    label: str,
    url_name: str,
    current_url_name: str | None,
):
    return {
        "label": label,
        "url": reverse(url_name),
        "active": current_url_name == url_name,
    }


def navigation(request):
    """Expone solo enlaces implementados y permitidos para el modo vigente."""

    if not request.user.is_authenticated:
        return {
            "active_mode": None,
            "active_mode_code": None,
            "nav_items": [],
        }

    active_mode = get_valid_active_mode(request)
    if not active_mode:
        return {
            "active_mode": None,
            "active_mode_code": None,
            "nav_items": [],
        }

    current_url_name = getattr(
        request.resolver_match,
        "view_name",
        None,
    )

    definitions = list(MODE_NAVIGATION[active_mode])

    if active_mode == ADMINISTRATOR and request.user.is_staff:
        definitions.extend(STAFF_ADMIN_NAVIGATION)

    return {
        "active_mode": ROLE_PRESENTATION[active_mode]["label"],
        "active_mode_code": active_mode,
        "active_dashboard_url": reverse(
            DASHBOARD_URL_NAMES[active_mode]
        ),
        "nav_items": [
            _navigation_item(
                label,
                url_name,
                current_url_name,
            )
            for label, url_name in definitions
        ],
    }