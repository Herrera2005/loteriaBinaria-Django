"""Contexto global de navegación, derivado exclusivamente del backend."""

from django.urls import reverse

from apps.accounts.access import get_valid_active_mode
from apps.accounts.roles import DASHBOARD_URL_NAMES, ROLE_PRESENTATION


def navigation(request):
    if not request.user.is_authenticated:
        return {"active_mode": None, "active_mode_code": None, "nav_items": []}

    active_mode = get_valid_active_mode(request)
    if not active_mode:
        return {"active_mode": None, "active_mode_code": None, "nav_items": []}

    url_name = DASHBOARD_URL_NAMES[active_mode]
    current_url_name = getattr(request.resolver_match, "view_name", None)
    return {
        "active_mode": ROLE_PRESENTATION[active_mode]["label"],
        "active_mode_code": active_mode,
        "nav_items": [
            {
                "label": f"Panel {ROLE_PRESENTATION[active_mode]['label']}",
                "url": reverse(url_name),
                "active": current_url_name == url_name,
            }
        ],
    }
