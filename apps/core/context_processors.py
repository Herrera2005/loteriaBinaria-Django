"""Contexto global de navegación calculado exclusivamente en backend."""

from django.urls import reverse

from apps.accounts.policies import assigned_role_codes, get_active_mode
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
        ("Sorteos", "lottery:client_event_list"),
        ("Mis boletos", "lottery:client_ticket_list"),
        ("Billeteras y movimientos", "finance:wallet_detail"),
        ("Operaciones REAL", "finance:real_operations"),
        ("Conversión de wallets", "finance:wallet_conversion"),
        ("Mis solicitudes", "vendors:client_conversionrequest_list"),
        ("Transferir VIRTUAL", "finance:virtual_transfer"),
    ),
    VENDOR: (
        ("Panel Vendedor", "core:vendor_dashboard"),
        ("Operaciones REAL", "finance:vendor_real_operations"),
        ("Monedas e inventario", "finance:vendor_currency_operations"),
        ("Mi inventario", "finance:vendor_inventory"),
        ("Solicitudes", "core:vendor_requests"),
        ("Billeteras y movimientos", "finance:wallet_detail"),
    ),
    ADMINISTRATOR: (
        ("Panel Administrador", "core:admin_dashboard"),
        ("Billeteras y movimientos", "finance:wallet_detail"),
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
            "can_switch_mode": False,
        }

    assigned_mode_count = len(assigned_role_codes(request.user))
    can_switch_mode = assigned_mode_count > 1

    active_mode = get_active_mode(request)
    if not active_mode:
        return {
            "active_mode": None,
            "active_mode_code": None,
            "nav_items": [],
            "can_switch_mode": can_switch_mode,
        }

    current_url_name = getattr(request.resolver_match, "view_name", None)
    definitions = list(MODE_NAVIGATION[active_mode])

    if active_mode == ADMINISTRATOR and request.user.is_staff:
        definitions.extend(STAFF_ADMIN_NAVIGATION)

    return {
        "active_mode": ROLE_PRESENTATION[active_mode]["label"],
        "active_mode_code": active_mode,
        "active_dashboard_url": reverse(DASHBOARD_URL_NAMES[active_mode]),
        "nav_items": [
            _navigation_item(label, url_name, current_url_name)
            for label, url_name in definitions
        ],
        "can_switch_mode": can_switch_mode,
    }
