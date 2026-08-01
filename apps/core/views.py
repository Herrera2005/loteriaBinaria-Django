"""Vistas públicas y paneles que ya tienen rutas verificables."""

from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.urls import reverse

from apps.accounts.access import active_mode_required, get_valid_active_mode
from apps.accounts.roles import ADMINISTRATOR, CLIENT, DASHBOARD_URL_NAMES, VENDOR


def home(request):
    dashboard_url = None
    if request.user.is_authenticated:
        active_mode = get_valid_active_mode(request)
        if active_mode:
            dashboard_url = reverse(DASHBOARD_URL_NAMES[active_mode])
        else:
            dashboard_url = reverse("accounts:choose_mode")
    return render(
        request,
        "core/home.html",
        {
            "dashboard_url": dashboard_url,
            "products": [],
        },
    )


@active_mode_required(CLIENT)
def client_dashboard(request):
    return render(
        request,
        "dashboards/client.html",
        {
            "choose_mode_url": reverse("accounts:choose_mode"),
            "real_available_display": "—",
            "virtual_available_display": "—",
            "ticket_count": 0,
            "active_request_count": 0,
            "client_actions": [],
            "available_events": [],
            "tickets": [],
            "ticket_product_options": [],
            "ticket_status_options": [],
            "ticket_filters": {
                "date_from": request.GET.get("date_from", ""),
                "q": request.GET.get("q", ""),
            },
            "recent_movements": [],
            "recent_requests": [],
            "backend_modules_pending": True,
        },
    )


@active_mode_required(VENDOR)
def vendor_dashboard(request):
    return render(
        request,
        "dashboards/vendor.html",
        {
            "choose_mode_url": reverse("accounts:choose_mode"),
            "real_available_display": "—",
            "virtual_available_display": "—",
            "pending_request_count": 0,
            "completed_request_count": 0,
            "vendor_actions": [],
            "assigned_requests": [],
            "recent_movements": [],
            "backend_modules_pending": True,
        },
    )


@active_mode_required(ADMINISTRATOR)
def admin_dashboard(request):
    User = get_user_model()
    admin_access_ready = request.user.is_staff
    admin_sections = []
    history_links = []
    django_admin_url = None
    active_user_count = None
    active_vendor_count = None

    if admin_access_ready:
        django_admin_url = reverse("admin:index")
        active_user_count = User.objects.filter(
            is_active=True,
            status=User.Status.ACTIVE,
        ).count()
        active_vendor_count = User.objects.filter(
            is_active=True,
            status=User.Status.ACTIVE,
            groups__name=VENDOR,
        ).distinct().count()
        admin_sections = [
            {
                "label": "Usuarios",
                "description": "Administrar cuentas sin borrado físico.",
                "url": reverse("admin:accounts_user_changelist"),
                "count": User.objects.count(),
            },
            {
                "label": "Versiones legales",
                "description": "Términos y privacidad versionados.",
                "url": reverse("admin:accounts_termsversion_changelist"),
                "count": None,
            },
        ]
        history_links = [
            {
                "label": "Aceptaciones históricas",
                "url": reverse("admin:accounts_termsacceptance_changelist"),
            }
        ]

    return render(
        request,
        "dashboards/admin.html",
        {
            "choose_mode_url": reverse("accounts:choose_mode"),
            "django_admin_url": django_admin_url,
            "admin_access_ready": admin_access_ready,
            "active_user_count": active_user_count,
            "active_vendor_count": active_vendor_count,
            "admin_sections": admin_sections,
            "history_links": history_links,
            "backend_modules_pending": True,
        },
    )
