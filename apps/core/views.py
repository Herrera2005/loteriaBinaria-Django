"""Landing, dashboards y auditoría read-only del Taller #3."""

from __future__ import annotations

from datetime import date

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from apps.accounts.access import active_mode_required, get_valid_active_mode
from apps.accounts.roles import ADMINISTRATOR, CLIENT, DASHBOARD_URL_NAMES, VENDOR
from apps.finance.models import Movement, Wallet
from apps.lottery.models import DrawEvent, LotteryProduct, Ticket
from apps.vendors.models import (
    ConversionAssignment,
    ConversionRequest,
    VendorProfile,
)
from apps.vendors.services import (
    assign_conversion_request,
    complete_conversion_request,
    eligible_conversion_requests,
    release_conversion_assignment,
)

from .date_utils import local_date_bounds
from .models import AuditEvent


AUDIT_EVENTS_PER_PAGE = 20

@require_GET
def start_redirect(request):
    """Dirige al inicio público, selector o dashboard según la sesión."""

    if not request.user.is_authenticated:
        return redirect("core:home")

    active_mode = get_valid_active_mode(request)
    if active_mode is None:
        return redirect("accounts:choose_mode")

    return redirect(DASHBOARD_URL_NAMES[active_mode])


def _format_minor(amount_minor: int, currency: str, *, signed: bool = False) -> str:
    """Formatea enteros minor para presentación, sin usar float."""

    value = int(amount_minor)
    sign = ""
    if signed and value > 0:
        sign = "+"
    elif value < 0:
        sign = "-"

    major, minor = divmod(abs(value), 100)
    prefix = "$" if currency == Wallet.Currency.REAL else "V"
    return f"{sign}{prefix} {major:,}.{minor:02d}"


def _parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _query_without_page(request) -> str:
    query = request.GET.copy()
    query.pop("page", None)
    return query.urlencode()


def _wallet_map(user) -> dict[str, Wallet]:
    return {
        wallet.currency: wallet
        for wallet in (
            Wallet.objects
            .filter(user=user)
            .order_by("currency")
        )
    }


def _wallet_summary(user) -> dict[str, object]:
    wallets = _wallet_map(user)
    real_wallet = wallets.get(Wallet.Currency.REAL)
    virtual_wallet = wallets.get(Wallet.Currency.VIRTUAL)

    return {
        "real_wallet": real_wallet,
        "virtual_wallet": virtual_wallet,
        "real_available_display": (
            _format_minor(real_wallet.available_minor, real_wallet.currency)
            if real_wallet
            else "No disponible"
        ),
        "real_reserved_display": (
            _format_minor(real_wallet.reserved_minor, real_wallet.currency)
            if real_wallet
            else "No disponible"
        ),
        "virtual_available_display": (
            _format_minor(
                virtual_wallet.available_minor,
                virtual_wallet.currency,
            )
            if virtual_wallet
            else "No disponible"
        ),
        "virtual_reserved_display": (
            _format_minor(
                virtual_wallet.reserved_minor,
                virtual_wallet.currency,
            )
            if virtual_wallet
            else "No disponible"
        ),
    }


def _movement_rows(user, *, limit: int = 5) -> list[dict[str, object]]:
    movements = (
        Movement.objects
        .filter(wallet__user=user)
        .select_related("wallet")
        .order_by("-created_at", "-id")[:limit]
    )

    rows = []
    for movement in movements:
        signed_amount = movement.amount_minor
        if movement.direction == Movement.Direction.DEBIT:
            signed_amount *= -1

        rows.append(
            {
                "movement": movement,
                "type_label": movement.get_type_display(),
                "direction": movement.direction,
                "direction_label": movement.get_direction_display(),
                "currency_label": movement.wallet.get_currency_display(),
                "amount_display": _format_minor(
                    signed_amount,
                    movement.wallet.currency,
                    signed=True,
                ),
            }
        )
    return rows


def _visible_event_rows(*, limit: int = 6) -> list[dict[str, object]]:
    """Devuelve sorteos visibles, con abiertos primero y estado visual explícito."""

    now = timezone.now()
    events = (
        DrawEvent.objects
        .filter(
            product__is_active=True,
            status__in=(
                DrawEvent.Status.SCHEDULED,
                DrawEvent.Status.PUBLISHED,
                DrawEvent.Status.SALES_OPEN,
            ),
            sales_close_at__gt=now,
        )
        .select_related("product")
        .annotate(
            open_rank=Case(
                When(status=DrawEvent.Status.SALES_OPEN, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("open_rank", "sales_close_at", "draw_at", "id")[:limit]
    )

    rows = []
    for event in events:
        is_open_now = (
            event.status == DrawEvent.Status.SALES_OPEN
            and now < event.sales_close_at
        )
        is_upcoming = (
            event.status in (
                DrawEvent.Status.SCHEDULED,
                DrawEvent.Status.PUBLISHED,
            )
            and event.sales_open_at > now
        )
        rows.append(
            {
                "event": event,
                "product_label": event.product.name,
                "status_label": event.get_status_display(),
                "is_open_now": is_open_now,
                "is_upcoming": is_upcoming,
                "price_display": _format_minor(
                    event.price_minor,
                    Wallet.Currency.VIRTUAL,
                ),
                "prize_display": _format_minor(
                    event.prize_minor,
                    Wallet.Currency.VIRTUAL,
                ),
            }
        )
    return rows


def home(request):
    dashboard_url = None
    if request.user.is_authenticated:
        active_mode = get_valid_active_mode(request)
        if active_mode:
            dashboard_url = reverse(DASHBOARD_URL_NAMES[active_mode])
        else:
            dashboard_url = reverse("accounts:choose_mode")

    products = LotteryProduct.objects.filter(is_active=True).order_by("id")

    return render(
        request,
        "core/home.html",
        {
            "dashboard_url": dashboard_url,
            "products": products,
        },
    )


@active_mode_required(CLIENT)
def client_dashboard(request):
    wallet_context = _wallet_summary(request.user)

    active_request_count = (
        ConversionRequest.objects
        .filter(client=request.user)
        .exclude(status__in=ConversionRequest.TERMINAL_STATUSES)
        .count()
    )

    recent_tickets = (
        Ticket.objects
        .filter(user=request.user)
        .select_related("event", "event__product")
        .order_by("-created_at", "-id")[:5]
    )
    ticket_rows = [
        {
            "ticket": ticket,
            "product_label": ticket.event.product.name,
            "ownership_label": ticket.get_ownership_status_display(),
            "evaluation_label": ticket.get_evaluation_status_display(),
            "price_display": _format_minor(
                ticket.price_minor,
                Wallet.Currency.VIRTUAL,
            ),
        }
        for ticket in recent_tickets
    ]

    recent_requests = (
        ConversionRequest.objects
        .filter(client=request.user)
        .order_by("-created_at", "-id")[:5]
    )
    request_rows = [
        {
            "request": request_item,
            "status_label": request_item.get_status_display(),
            "amount_display": _format_minor(
                request_item.amount_minor,
                Wallet.Currency.REAL,
            ),
        }
        for request_item in recent_requests
    ]

    context = {
        "choose_mode_url": reverse("accounts:choose_mode"),
        "wallet_url": reverse("finance:wallet_detail"),
        "movement_url": reverse("finance:movement_list"),
        "ticket_count": Ticket.objects.filter(user=request.user).count(),
        "active_request_count": active_request_count,
        "available_events": _visible_event_rows(),
        "recent_tickets": ticket_rows,
        "recent_requests": request_rows,
        "recent_movements": _movement_rows(request.user),
    }
    context.update(wallet_context)

    return render(request, "dashboards/client.html", context)


@active_mode_required(VENDOR)
def vendor_dashboard(request):
    wallet_context = _wallet_summary(request.user)
    vendor_profile = (
        VendorProfile.objects
        .filter(user=request.user)
        .first()
    )

    pending_request_count = 0
    completed_request_count = 0
    assigned_request_rows = []

    if vendor_profile is not None:
        assignments = (
            ConversionAssignment.objects
            .filter(vendor=vendor_profile)
            .select_related("request", "request__client")
            .order_by("-assigned_at", "-id")
        )
        pending_request_count = assignments.filter(
            status=ConversionAssignment.Status.ACTIVE,
        ).count()
        completed_request_count = assignments.filter(
            status=ConversionAssignment.Status.COMPLETED,
        ).count()

        assigned_request_rows = [
            {
                "assignment": assignment,
                "request": assignment.request,
                "client_label": assignment.request.client.username,
                "amount_display": _format_minor(
                    assignment.request.amount_minor,
                    Wallet.Currency.REAL,
                ),
                "request_status_label": (
                    assignment.request.get_status_display()
                ),
                "assignment_status_label": assignment.get_status_display(),
                "can_complete": (
                    assignment.status == ConversionAssignment.Status.ACTIVE
                    and assignment.request.status
                    == ConversionRequest.Status.IN_PROGRESS
                    and assignment.request.expires_at > timezone.now()
                ),
                "can_release": (
                    assignment.status == ConversionAssignment.Status.ACTIVE
                    and assignment.request.status
                    == ConversionRequest.Status.IN_PROGRESS
                    and assignment.request.expires_at > timezone.now()
                ),
            }
            for assignment in assignments[:5]
        ]

    context = {
        "choose_mode_url": reverse("accounts:choose_mode"),
        "wallet_url": reverse("finance:wallet_detail"),
        "movement_url": reverse("finance:movement_list"),
        "vendor_real_operations_url": reverse(
            "finance:vendor_real_operations"
        ),
        "vendor_currency_operations_url": reverse(
            "finance:vendor_currency_operations"
        ),
        "vendor_inventory_url": reverse("finance:vendor_inventory"),
        "vendor_requests_url": reverse("core:vendor_requests"),
        "vendor_profile": vendor_profile,
        "pending_request_count": pending_request_count,
        "completed_request_count": completed_request_count,
        "assigned_requests": assigned_request_rows,
        "recent_movements": _movement_rows(request.user),
    }
    context.update(wallet_context)

    return render(request, "dashboards/vendor.html", context)


@active_mode_required(VENDOR)
@require_http_methods(["GET", "POST"])
def vendor_requests(request):
    """Cola elegible y asignaciones propias del vendedor."""

    vendor_profile = (
        VendorProfile.objects
        .filter(user=request.user)
        .first()
    )

    if request.method == "POST":
        action = request.POST.get("action", "take")

        try:
            if action == "complete":
                assignment_id = int(request.POST.get("assignment_id", ""))
                assignment, completed_now = complete_conversion_request(
                    vendor=request.user,
                    assignment_id=assignment_id,
                )
                if completed_now:
                    messages.success(
                        request,
                        (
                            "Solicitud completada. El Cliente recibió VIRTUAL "
                            "y el Vendedor recibió REAL."
                        ),
                    )
                else:
                    messages.info(
                        request,
                        f"La asignación #{assignment.pk} ya estaba completada.",
                    )
            elif action == "release":
                assignment_id = int(request.POST.get("assignment_id", ""))
                assignment, released_now = release_conversion_assignment(
                    vendor=request.user,
                    assignment_id=assignment_id,
                )
                if released_now:
                    messages.success(
                        request,
                        (
                            "Asignación liberada. El VIRTUAL volvió a tu "
                            "saldo disponible y la solicitud quedó disponible "
                            "para otro vendedor."
                        ),
                    )
                else:
                    messages.info(
                        request,
                        f"La asignación #{assignment.pk} ya estaba liberada.",
                    )
            elif action == "take":
                request_id = int(request.POST.get("request_id", ""))
                assignment = assign_conversion_request(
                    vendor=request.user,
                    request_id=request_id,
                )
                messages.success(
                    request,
                    (
                        "Solicitud tomada correctamente. "
                        f"Asignación #{assignment.pk} creada."
                    ),
                )
            else:
                raise ValidationError("La acción indicada no es válida.")
        except (TypeError, ValueError):
            messages.error(request, "El identificador indicado no es válido.")
        except ValidationError as exc:
            message = (
                exc.messages[0]
                if getattr(exc, "messages", None)
                else str(exc)
            )
            messages.error(request, message)

        if action in {"complete", "release"}:
            return redirect(f'{reverse("core:vendor_requests")}?tab=mine')
        return redirect("core:vendor_requests")

    requested_tab = request.GET.get("tab", "available")
    active_tab = requested_tab if requested_tab in {"available", "mine"} else "available"

    available_rows = []
    assignment_rows = []

    if vendor_profile is not None and vendor_profile.status == VendorProfile.Status.ACTIVE:
        available_rows = [
            {
                "request": item,
                "client_label": f"Cliente #{item.client_id}",
                "amount_display": _format_minor(
                    item.amount_minor,
                    Wallet.Currency.VIRTUAL,
                ),
            }
            for item in eligible_conversion_requests(vendor=request.user)
        ]

        assignments = (
            ConversionAssignment.objects
            .filter(vendor=vendor_profile)
            .select_related("request", "request__client")
            .order_by("-assigned_at", "-id")
        )
        assignment_rows = [
            {
                "assignment": assignment,
                "request": assignment.request,
                "client_label": f"Cliente #{assignment.request.client_id}",
                "amount_display": _format_minor(
                    assignment.request.amount_minor,
                    Wallet.Currency.VIRTUAL,
                ),
                "request_status_label": assignment.request.get_status_display(),
                "assignment_status_label": assignment.get_status_display(),
                "can_complete": (
                    assignment.status == ConversionAssignment.Status.ACTIVE
                    and assignment.request.status
                    == ConversionRequest.Status.IN_PROGRESS
                    and assignment.request.expires_at > timezone.now()
                ),
                "can_release": (
                    assignment.status == ConversionAssignment.Status.ACTIVE
                    and assignment.request.status
                    == ConversionRequest.Status.IN_PROGRESS
                    and assignment.request.expires_at > timezone.now()
                ),
            }
            for assignment in assignments
        ]

    return render(
        request,
        "core/vendor_requests.html",
        {
            "vendor_profile": vendor_profile,
            "available_rows": available_rows,
            "assignment_rows": assignment_rows,
            "active_tab": active_tab,
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
                "description": "Administrar cuentas sin borrar historia.",
                "url": reverse("accounts:user_list"),
                "count": User.objects.count(),
            },
            {
                "label": "Perfiles de vendedores",
                "description": "Gestionar habilitaciones de vendedores.",
                "url": reverse("vendors:vendorprofile_list"),
                "count": VendorProfile.objects.count(),
            },
            {
                "label": "Solicitudes de conversión",
                "description": "Consultar solicitudes históricas read-only.",
                "url": reverse("vendors:conversionrequest_list"),
                "count": ConversionRequest.objects.count(),
            },
            {
                "label": "Productos de lotería",
                "description": "Gestionar Octal, Decimal y Hexadecimal.",
                "url": reverse("lottery:product_list"),
                "count": LotteryProduct.objects.count(),
            },
            {
                "label": "Eventos de sorteo",
                "description": "Gestionar eventos y bloqueos históricos.",
                "url": reverse("lottery:event_list"),
                "count": DrawEvent.objects.count(),
            },
        ]
        history_links = [
            {
                "label": "Versiones legales",
                "url": reverse("admin:accounts_termsversion_changelist"),
            },
            {
                "label": "Aceptaciones históricas",
                "url": reverse("admin:accounts_termsacceptance_changelist"),
            },
            {
                "label": "Wallets read-only",
                "url": reverse("admin:finance_wallet_changelist"),
            },
            {
                "label": "Movimientos read-only",
                "url": reverse("admin:finance_movement_changelist"),
            },
        ]

    recent_audit_events = (
        AuditEvent.objects
        .select_related("actor")
        .order_by("-created_at", "-id")[:5]
    )

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
            "audit_url": reverse("core:audit_list"),
            "wallet_url": reverse("finance:wallet_detail"),
            "movement_url": reverse("finance:movement_list"),
            "audit_event_count": AuditEvent.objects.count(),
            "recent_audit_events": recent_audit_events,
        },
    )


@active_mode_required(ADMINISTRATOR)
@require_GET
def audit_list(request):
    queryset = (
        AuditEvent.objects
        .select_related("actor")
        .order_by("-created_at", "-id")
    )

    query = request.GET.get("q", "").strip()
    if query:
        queryset = queryset.filter(
            Q(actor__username__icontains=query)
            | Q(action__icontains=query)
            | Q(resource_type__icontains=query)
            | Q(resource_id__icontains=query)
            | Q(reason__icontains=query)
        )

    selected_mode = request.GET.get("mode", "").strip()
    valid_modes = {value for value, _ in AuditEvent.ActiveMode.choices}
    if selected_mode in valid_modes:
        queryset = queryset.filter(active_mode=selected_mode)
    else:
        selected_mode = ""

    selected_action = request.GET.get("action", "").strip()
    available_actions = list(
        AuditEvent.objects
        .exclude(action="")
        .order_by("action")
        .values_list("action", flat=True)
        .distinct()
    )
    if selected_action in available_actions:
        queryset = queryset.filter(action=selected_action)
    else:
        selected_action = ""

    selected_resource = request.GET.get("resource_type", "").strip()
    available_resources = list(
        AuditEvent.objects
        .exclude(resource_type="")
        .order_by("resource_type")
        .values_list("resource_type", flat=True)
        .distinct()
    )
    if selected_resource in available_resources:
        queryset = queryset.filter(resource_type=selected_resource)
    else:
        selected_resource = ""

    date_from_value = request.GET.get("date_from", "").strip()
    date_from = _parse_iso_date(date_from_value)
    if date_from is not None:
        date_from_start, _ = local_date_bounds(date_from)
        queryset = queryset.filter(created_at__gte=date_from_start)
    else:
        date_from_value = ""

    date_to_value = request.GET.get("date_to", "").strip()
    date_to = _parse_iso_date(date_to_value)
    if date_to is not None:
        _, date_to_end = local_date_bounds(date_to)
        queryset = queryset.filter(created_at__lt=date_to_end)
    else:
        date_to_value = ""

    paginator = Paginator(queryset, AUDIT_EVENTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "core/audit_list.html",
        {
            "audit_events": page_obj.object_list,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "mode_choices": AuditEvent.ActiveMode.choices,
            "available_actions": available_actions,
            "available_resources": available_resources,
            "query": query,
            "selected_mode": selected_mode,
            "selected_action": selected_action,
            "selected_resource": selected_resource,
            "date_from": date_from_value,
            "date_to": date_to_value,
            "query_without_page": _query_without_page(request),
        },
    )


@active_mode_required(ADMINISTRATOR)
@require_GET
def audit_detail(request, pk: int):
    audit_event = get_object_or_404(
        AuditEvent.objects.select_related("actor"),
        pk=pk,
    )
    return render(
        request,
        "core/audit_detail.html",
        {"audit_event": audit_event},
    )
