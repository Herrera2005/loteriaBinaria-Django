"""Consultas y operaciones financieras del usuario autenticado."""

from __future__ import annotations

from datetime import date
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from apps.accounts.access import get_valid_active_mode
from apps.accounts.policies import can_use_vendor_functions
from apps.accounts.models import User
from apps.accounts.roles import CLIENT, DASHBOARD_URL_NAMES, VENDOR
from apps.core.date_utils import local_date_bounds
from apps.vendors.forms import ConversionRequestCreateForm
from apps.vendors.services import create_conversion_request

from .forms import (
    ConversionForm,
    TopUpForm,
    VirtualTransferForm,
    WithdrawalForm,
    VendorInventoryPurchaseForm,
)
from .models import Movement, VendorInventoryPurchase, Wallet
from .services import (
    confirm_topup,
    confirm_withdrawal,
    convert_virtual_to_real,
    transfer_virtual,
    confirm_vendor_topup,
    confirm_vendor_withdrawal,
    convert_vendor_virtual_to_real,
    purchase_vendor_inventory,
)


MOVEMENTS_PER_PAGE = 15


def _operational_mode_required(view_func):
    """Exige cuenta activa y algún modo válido para consultas propias."""

    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_active or user.status != User.Status.ACTIVE:
            raise PermissionDenied(
                "La cuenta no está activa para consultar finanzas."
            )

        if get_valid_active_mode(request) is None:
            return redirect("accounts:choose_mode")

        return view_func(request, *args, **kwargs)

    return wrapped


def _client_mode_required(view_func):
    """Restringe operaciones de Cliente al rol y modo CLIENTE."""

    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_active or user.status != User.Status.ACTIVE:
            raise PermissionDenied("La cuenta no está activa.")

        active_mode = get_valid_active_mode(request)
        if active_mode is None:
            return redirect("accounts:choose_mode")

        has_client_role = user.groups.filter(name=CLIENT).exists()
        if active_mode != CLIENT or not has_client_role:
            raise PermissionDenied(
                "Esta operación requiere el modo CLIENTE."
            )

        return view_func(request, *args, **kwargs)

    return wrapped


def _vendor_mode_required(view_func):
    """Restringe operaciones al rol, modo y perfil VENDEDOR activos."""

    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_active or user.status != User.Status.ACTIVE:
            raise PermissionDenied("La cuenta no está activa.")

        active_mode = get_valid_active_mode(request)
        if active_mode is None:
            return redirect("accounts:choose_mode")

        if not can_use_vendor_functions(request):
            raise PermissionDenied(
                "Esta operación requiere el modo VENDEDOR."
            )

        from apps.vendors.models import VendorProfile

        profile = VendorProfile.objects.filter(user=user).first()
        if profile is None or profile.status != VendorProfile.Status.ACTIVE:
            raise PermissionDenied(
                "Se requiere un perfil vendedor activo."
            )

        return view_func(request, *args, **kwargs)

    return wrapped


def _format_minor(
    amount_minor: int,
    currency: str,
    *,
    signed: bool = False,
) -> str:
    """Formatea unidades menores sin usar float."""

    value = int(amount_minor)
    sign = ""
    if signed and value > 0:
        sign = "+"
    elif value < 0:
        sign = "-"

    major, minor = divmod(abs(value), 100)
    prefix = "$" if currency == Wallet.Currency.REAL else "V"
    return f"{sign}{prefix} {major:,}.{minor:02d}"


def _dashboard_url(request) -> str:
    active_mode = get_valid_active_mode(request)
    return reverse(DASHBOARD_URL_NAMES[active_mode])


def _wallet_card(wallet: Wallet) -> dict[str, object]:
    total_minor = wallet.available_minor + wallet.reserved_minor
    return {
        "wallet": wallet,
        "currency": wallet.currency,
        "currency_label": wallet.get_currency_display(),
        "available_display": _format_minor(
            wallet.available_minor,
            wallet.currency,
        ),
        "reserved_display": _format_minor(
            wallet.reserved_minor,
            wallet.currency,
        ),
        "total_display": _format_minor(total_minor, wallet.currency),
        "status": wallet.status,
        "status_label": wallet.get_status_display(),
    }


def _wallet_summary(user) -> dict[str, object]:
    """Resumen solo lectura de las dos wallets para pantallas operativas."""

    wallet_map = {
        wallet.currency: wallet
        for wallet in Wallet.objects.filter(user=user).order_by("currency")
    }

    summary: dict[str, object] = {
        "wallet_cards": [],
        "missing_currencies": [],
        "real_wallet": None,
        "virtual_wallet": None,
    }

    for currency, label in Wallet.Currency.choices:
        wallet = wallet_map.get(currency)
        if wallet is None:
            summary["missing_currencies"].append(label)
            continue

        card = _wallet_card(wallet)
        summary["wallet_cards"].append(card)
        if currency == Wallet.Currency.REAL:
            summary["real_wallet"] = card
        else:
            summary["virtual_wallet"] = card

    return summary


def _movement_row(movement: Movement) -> dict[str, object]:
    signed_amount = movement.amount_minor
    if movement.direction == Movement.Direction.DEBIT:
        signed_amount *= -1

    return {
        "movement": movement,
        "currency": movement.wallet.currency,
        "currency_label": movement.wallet.get_currency_display(),
        "type_label": movement.get_type_display(),
        "direction": movement.direction,
        "direction_label": movement.get_direction_display(),
        "amount_display": _format_minor(
            signed_amount,
            movement.wallet.currency,
            signed=True,
        ),
        "balance_after_display": _format_minor(
            movement.balance_after_minor,
            movement.wallet.currency,
        ),
    }


def _parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _query_without_page(request) -> str:
    query = request.GET.copy()
    query.pop("page", None)
    return query.urlencode()


@_operational_mode_required
@require_GET
def wallet_detail(request):
    """Unifica saldos y movimientos propios en una sola sección."""

    active_tab = request.GET.get("tab", "balances")
    if active_tab not in {"balances", "movements"}:
        active_tab = "balances"

    context = _wallet_summary(request.user)
    context.update(_movement_context(request))
    context.update(
        {
            "active_tab": active_tab,
            "dashboard_url": _dashboard_url(request),
            "can_use_client_finance": (
                get_valid_active_mode(request) == CLIENT
            ),
        }
    )
    return render(request, "finance/wallet_detail.html", context)


def _movement_context(request) -> dict[str, object]:
    """Construye filtros y paginación de movimientos del usuario actual."""

    queryset = (
        Movement.objects
        .filter(wallet__user=request.user)
        .select_related("wallet")
        .order_by("-created_at", "-id")
    )

    selected_currency = request.GET.get("currency", "").strip()
    valid_currencies = {value for value, _ in Wallet.Currency.choices}
    if selected_currency in valid_currencies:
        queryset = queryset.filter(wallet__currency=selected_currency)
    else:
        selected_currency = ""

    selected_type = request.GET.get("type", "").strip()
    valid_types = {value for value, _ in Movement.Type.choices}
    if selected_type in valid_types:
        queryset = queryset.filter(type=selected_type)
    else:
        selected_type = ""

    selected_direction = request.GET.get("direction", "").strip()
    valid_directions = {value for value, _ in Movement.Direction.choices}
    if selected_direction in valid_directions:
        queryset = queryset.filter(direction=selected_direction)
    else:
        selected_direction = ""

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

    page_obj = Paginator(queryset, MOVEMENTS_PER_PAGE).get_page(
        request.GET.get("page")
    )

    return {
        "movement_rows": [
            _movement_row(movement)
            for movement in page_obj.object_list
        ],
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "currency_choices": Wallet.Currency.choices,
        "type_choices": Movement.Type.choices,
        "direction_choices": Movement.Direction.choices,
        "selected_currency": selected_currency,
        "selected_type": selected_type,
        "selected_direction": selected_direction,
        "date_from": date_from_value,
        "date_to": date_to_value,
        "query_without_page": _query_without_page(request),
    }


@_operational_mode_required
@require_GET
def movement_list(request):
    """Compatibilidad: abre la pestaña Movimientos de la sección unificada."""

    query = request.GET.copy()
    query["tab"] = "movements"
    target = reverse("finance:wallet_detail")
    encoded = query.urlencode()
    return redirect(f"{target}?{encoded}" if encoded else target)


@_client_mode_required
@require_http_methods(["GET", "POST"])
def real_operations(request):
    """Agrupa recarga y retiro REAL mediante pestañas de una sola página."""

    requested_tab = request.GET.get("tab", "topup")
    active_tab = requested_tab if requested_tab in {"topup", "withdrawal"} else "topup"

    action = request.POST.get("action", "")
    topup_form = TopUpForm(
        request.POST if action == "topup" else None,
        prefix="topup",
    )
    withdrawal_form = WithdrawalForm(
        request.POST if action == "withdrawal" else None,
        prefix="withdrawal",
    )

    if request.method == "POST":
        if action == "topup":
            active_tab = "topup"
            if topup_form.is_valid():
                try:
                    _, created = confirm_topup(
                        user=request.user,
                        amount_minor=topup_form.amount_minor(),
                        operation_id=topup_form.cleaned_data["operation_id"],
                    )
                except ValidationError as exc:
                    topup_form.add_error(None, exc)
                else:
                    if created:
                        messages.success(
                            request,
                            "Recarga REAL confirmada 1:1.",
                        )
                    else:
                        messages.info(
                            request,
                            "La recarga ya estaba confirmada; no se duplicó.",
                        )
                    return redirect(f"{reverse('finance:wallet_detail')}?tab=movements")

        elif action == "withdrawal":
            active_tab = "withdrawal"
            if withdrawal_form.is_valid():
                try:
                    _, created = confirm_withdrawal(
                        user=request.user,
                        amount_minor=withdrawal_form.amount_minor(),
                        operation_id=(
                            withdrawal_form.cleaned_data["operation_id"]
                        ),
                    )
                except ValidationError as exc:
                    withdrawal_form.add_error(None, exc)
                else:
                    if created:
                        messages.success(
                            request,
                            "Retiro académico confirmado sin comisión adicional.",
                        )
                    else:
                        messages.info(
                            request,
                            "El retiro ya estaba confirmado; no se duplicó.",
                        )
                    return redirect(f"{reverse('finance:wallet_detail')}?tab=movements")
        else:
            raise PermissionDenied("Operación REAL no reconocida.")

    context = _wallet_summary(request.user)
    context.update(
        {
            "topup_form": topup_form,
            "withdrawal_form": withdrawal_form,
            "active_tab": active_tab,
            "dashboard_url": _dashboard_url(request),
        }
    )
    return render(request, "finance/real_operations.html", context)


@_client_mode_required
@require_http_methods(["GET", "POST"])
def wallet_conversion(request):
    """Agrupa VIRTUAL→REAL y explica REAL→VIRTUAL por solicitud."""

    requested_tab = request.GET.get("tab", "real-to-virtual")
    active_tab = (
        requested_tab
        if requested_tab in {"virtual-to-real", "real-to-virtual"}
        else "real-to-virtual"
    )

    action = request.POST.get("action", "")
    conversion_form = ConversionForm(
        request.POST if action == "virtual-to-real" else None,
        prefix="conversion",
    )
    request_form = ConversionRequestCreateForm(
        request.POST if action == "real-to-virtual" else None,
        prefix="request",
    )

    if request.method == "POST":
        if action == "virtual-to-real":
            active_tab = "virtual-to-real"
            if conversion_form.is_valid():
                try:
                    _, created = convert_virtual_to_real(
                        user=request.user,
                        gross_virtual_minor=conversion_form.amount_minor(),
                        operation_id=(
                            conversion_form.cleaned_data["operation_id"]
                        ),
                    )
                except ValidationError as exc:
                    conversion_form.add_error(None, exc)
                else:
                    if created:
                        messages.success(
                            request,
                            "Conversión VIRTUAL a REAL 90/10 confirmada.",
                        )
                    else:
                        messages.info(
                            request,
                            "La conversión ya estaba confirmada; no se duplicó.",
                        )
                    return redirect(f"{reverse('finance:wallet_detail')}?tab=movements")
        elif action == "real-to-virtual":
            active_tab = "real-to-virtual"
            if request_form.is_valid():
                try:
                    conversion_request, created = create_conversion_request(
                        client=request.user,
                        amount_minor=request_form.amount_minor(),
                        operation_id=(
                            request_form.cleaned_data["operation_id"]
                        ),
                    )
                except ValidationError as exc:
                    request_form.add_error(None, exc)
                else:
                    if created:
                        messages.success(
                            request,
                            "Solicitud creada y saldo REAL reservado.",
                        )
                    else:
                        messages.info(
                            request,
                            "La solicitud ya existía; no se duplicó la reserva.",
                        )
                    return redirect(
                        "vendors:client_conversionrequest_detail",
                        pk=conversion_request.pk,
                    )
        else:
            raise PermissionDenied("Operación de conversión no reconocida.")

    context = _wallet_summary(request.user)
    context.update(
        {
            "conversion_form": conversion_form,
            "request_form": request_form,
            "active_tab": active_tab,
            "dashboard_url": _dashboard_url(request),
        }
    )
    return render(request, "finance/wallet_conversion.html", context)


@_client_mode_required
@require_http_methods(["GET", "POST"])
def virtual_transfer(request):
    """Transfiere VIRTUAL entre cuentas Cliente activas."""

    form = VirtualTransferForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            _, created = transfer_virtual(
                sender=request.user,
                recipient_identifier=form.cleaned_data["recipient"],
                amount_minor=form.amount_minor(),
                operation_id=form.cleaned_data["operation_id"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            if created:
                messages.success(
                    request,
                    "Transferencia VIRTUAL confirmada.",
                )
            else:
                messages.info(
                    request,
                    "La transferencia ya estaba confirmada; no se duplicó.",
                )
            return redirect(f"{reverse('finance:wallet_detail')}?tab=movements")

    context = _wallet_summary(request.user)
    context.update(
        {
            "form": form,
            "dashboard_url": _dashboard_url(request),
        }
    )
    return render(request, "finance/transfer_form.html", context)


@_client_mode_required
@require_GET
def legacy_topup(request):
    """Conserva marcadores antiguos sin duplicar pantallas."""

    return redirect(f"{reverse('finance:real_operations')}?tab=topup")


@_client_mode_required
@require_GET
def legacy_withdrawal(request):
    """Conserva marcadores antiguos sin duplicar pantallas."""

    return redirect(f"{reverse('finance:real_operations')}?tab=withdrawal")


@_client_mode_required
@require_GET
def legacy_conversion(request):
    """Conserva marcadores antiguos sin duplicar pantallas."""

    return redirect(
        f"{reverse('finance:wallet_conversion')}?tab=virtual-to-real"
    )


@_vendor_mode_required
@require_http_methods(["GET", "POST"])
def vendor_real_operations(request):
    """Agrupa recarga y retiro REAL del vendedor en una sola página."""

    requested_tab = request.GET.get("tab", "topup")
    active_tab = (
        requested_tab
        if requested_tab in {"topup", "withdrawal"}
        else "topup"
    )
    action = request.POST.get("action", "")
    topup_form = TopUpForm(
        request.POST if action == "topup" else None,
        prefix="vendor-topup",
    )
    withdrawal_form = WithdrawalForm(
        request.POST if action == "withdrawal" else None,
        prefix="vendor-withdrawal",
    )

    if request.method == "POST":
        if action == "topup":
            active_tab = "topup"
            if topup_form.is_valid():
                try:
                    _, created = confirm_vendor_topup(
                        user=request.user,
                        amount_minor=topup_form.amount_minor(),
                        operation_id=topup_form.cleaned_data["operation_id"],
                    )
                except ValidationError as exc:
                    topup_form.add_error(None, exc)
                else:
                    messages.success(
                        request,
                        "Recarga REAL del vendedor confirmada."
                        if created
                        else "La recarga ya existía y no se duplicó.",
                    )
                    return redirect(f"{reverse('finance:wallet_detail')}?tab=movements")
        elif action == "withdrawal":
            active_tab = "withdrawal"
            if withdrawal_form.is_valid():
                try:
                    _, created = confirm_vendor_withdrawal(
                        user=request.user,
                        amount_minor=withdrawal_form.amount_minor(),
                        operation_id=(
                            withdrawal_form.cleaned_data["operation_id"]
                        ),
                    )
                except ValidationError as exc:
                    withdrawal_form.add_error(None, exc)
                else:
                    messages.success(
                        request,
                        "Retiro académico del vendedor confirmado."
                        if created
                        else "El retiro ya existía y no se duplicó.",
                    )
                    return redirect(f"{reverse('finance:wallet_detail')}?tab=movements")
        else:
            raise PermissionDenied("Operación REAL de vendedor no reconocida.")

    context = _wallet_summary(request.user)
    context.update(
        {
            "topup_form": topup_form,
            "withdrawal_form": withdrawal_form,
            "active_tab": active_tab,
            "dashboard_url": _dashboard_url(request),
        }
    )
    return render(request, "finance/vendor_real_operations.html", context)


@_vendor_mode_required
@require_http_methods(["GET", "POST"])
def vendor_currency_operations(request):
    """Compra mayorista y conversión VIRTUAL→REAL del vendedor."""

    requested_tab = request.GET.get("tab", "wholesale")
    active_tab = (
        requested_tab
        if requested_tab in {"wholesale", "virtual-to-real"}
        else "wholesale"
    )
    action = request.POST.get("action", "")
    purchase_form = VendorInventoryPurchaseForm(
        request.POST if action == "wholesale" else None,
        prefix="wholesale",
    )
    conversion_form = ConversionForm(
        request.POST if action == "virtual-to-real" else None,
        prefix="vendor-conversion",
    )

    if request.method == "POST":
        if action == "wholesale":
            active_tab = "wholesale"
            if purchase_form.is_valid():
                try:
                    purchase, created = purchase_vendor_inventory(
                        vendor=request.user,
                        virtual_minor=purchase_form.amount_minor(),
                        operation_id=(
                            purchase_form.cleaned_data["operation_id"]
                        ),
                    )
                except ValidationError as exc:
                    purchase_form.add_error(None, exc)
                else:
                    messages.success(
                        request,
                        (
                            "Compra mayorista confirmada: "
                            + _format_minor(
                                purchase.amount_minor,
                                Wallet.Currency.VIRTUAL,
                            )
                            + "."
                        )
                        if created
                        else "La compra ya existía y no se duplicó.",
                    )
                    return redirect("finance:vendor_inventory")
        elif action == "virtual-to-real":
            active_tab = "virtual-to-real"
            if conversion_form.is_valid():
                try:
                    _, created = convert_vendor_virtual_to_real(
                        user=request.user,
                        gross_virtual_minor=conversion_form.amount_minor(),
                        operation_id=(
                            conversion_form.cleaned_data["operation_id"]
                        ),
                    )
                except ValidationError as exc:
                    conversion_form.add_error(None, exc)
                else:
                    messages.success(
                        request,
                        "Conversión VIRTUAL a REAL 90/10 confirmada."
                        if created
                        else "La conversión ya existía y no se duplicó.",
                    )
                    return redirect(f"{reverse('finance:wallet_detail')}?tab=movements")
        else:
            raise PermissionDenied("Conversión de vendedor no reconocida.")

    context = _wallet_summary(request.user)
    context.update(
        {
            "purchase_form": purchase_form,
            "conversion_form": conversion_form,
            "active_tab": active_tab,
            "dashboard_url": _dashboard_url(request),
        }
    )
    return render(
        request,
        "finance/vendor_currency_operations.html",
        context,
    )


@_vendor_mode_required
@require_GET
def vendor_inventory(request):
    """Resumen e histórico propio del inventario mayorista."""

    purchases = (
        VendorInventoryPurchase.objects
        .filter(user=request.user)
        .order_by("-created_at", "-id")
    )
    page_obj = Paginator(purchases, MOVEMENTS_PER_PAGE).get_page(
        request.GET.get("page")
    )
    rows = [
        {
            "purchase": purchase,
            "virtual_display": _format_minor(
                purchase.amount_minor,
                Wallet.Currency.VIRTUAL,
            ),
            "cost_display": _format_minor(
                purchase.cost_real_minor,
                Wallet.Currency.REAL,
            ),
        }
        for purchase in page_obj.object_list
    ]
    context = _wallet_summary(request.user)
    context.update(
        {
            "purchase_rows": rows,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "dashboard_url": _dashboard_url(request),
        }
    )
    return render(request, "finance/vendor_inventory.html", context)
