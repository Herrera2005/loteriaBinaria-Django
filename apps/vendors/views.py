"""CRUD administrativo y consultas de solo lectura del módulo vendors."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from apps.accounts.access import assigned_mode_codes, get_valid_active_mode
from apps.accounts.models import User
from apps.accounts.policies import can_use_client_functions
from apps.accounts.roles import ADMINISTRATOR

from .forms import VendorProfileForm
from .models import ConversionRequest, VendorProfile
from .services import (
    cancel_conversion_request,
    remove_or_deactivate_vendor_profile,
    vendor_profile_has_history,
)


class AdministratorModeRequiredMixin(
    LoginRequiredMixin,
    UserPassesTestMixin,
):
    """Exige cuenta administrativa activa y modo ADMINISTRADOR."""

    raise_exception = True

    def test_func(self) -> bool:
        user = self.request.user
        if not user.is_authenticated:
            return False

        return (
            user.is_active
            and user.status == User.Status.ACTIVE
            and user.is_staff
            and ADMINISTRATOR in assigned_mode_codes(user)
            and get_valid_active_mode(self.request) == ADMINISTRATOR
        )

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


class VendorProfileListView(AdministratorModeRequiredMixin, ListView):
    model = VendorProfile
    template_name = "vendors/vendorprofile_list.html"
    context_object_name = "vendor_profiles"
    paginate_by = 15

    def get_queryset(self):
        queryset = (
            VendorProfile.objects
            .select_related("user")
            .annotate(assignments_count=Count("assignments"))
            .order_by("user__username")
        )

        selected_status = self.request.GET.get("status", "").strip()
        valid_statuses = {value for value, _ in VendorProfile.Status.choices}
        if selected_status in valid_statuses:
            queryset = queryset.filter(status=selected_status)

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(user__username__icontains=query)
                | Q(user__email__icontains=query)
                | Q(user__document__icontains=query)
                | Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_status = self.request.GET.get("status", "").strip()
        valid_statuses = {value for value, _ in VendorProfile.Status.choices}
        context.update(
            {
                "status_choices": VendorProfile.Status.choices,
                "selected_status": (
                    selected_status if selected_status in valid_statuses else ""
                ),
                "query": self.request.GET.get("q", "").strip(),
            }
        )
        return context


class VendorProfileDetailView(
    AdministratorModeRequiredMixin,
    DetailView,
):
    model = VendorProfile
    template_name = "vendors/vendorprofile_detail.html"
    context_object_name = "vendor_profile"

    def get_queryset(self):
        return VendorProfile.objects.select_related("user").prefetch_related(
            "user__groups",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignments = self.object.assignments.select_related("request").order_by(
            "-assigned_at",
            "-id",
        )
        context["assignments_page"] = Paginator(assignments, 15).get_page(
            self.request.GET.get("assignments_page")
        )
        context["has_history"] = vendor_profile_has_history(self.object)
        return context


class VendorProfileCreateView(
    AdministratorModeRequiredMixin,
    CreateView,
):
    model = VendorProfile
    form_class = VendorProfileForm
    template_name = "vendors/vendorprofile_form.html"

    def get_success_url(self):
        return reverse(
            "vendors:vendorprofile_detail",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            (
                f"Perfil vendedor de {self.object.user.username} "
                "creado correctamente."
            ),
        )
        return response


class VendorProfileUpdateView(
    AdministratorModeRequiredMixin,
    UpdateView,
):
    model = VendorProfile
    form_class = VendorProfileForm
    template_name = "vendors/vendorprofile_form.html"
    context_object_name = "vendor_profile"

    def get_success_url(self):
        return reverse(
            "vendors:vendorprofile_detail",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            (
                f"Perfil vendedor de {self.object.user.username} "
                "actualizado correctamente."
            ),
        )
        return response


class VendorProfileDeleteDeactivateView(
    AdministratorModeRequiredMixin,
    View,
):
    template_name = "vendors/vendorprofile_confirm_delete.html"

    def get_object(self) -> VendorProfile:
        return get_object_or_404(
            VendorProfile.objects.select_related("user"),
            pk=self.kwargs["pk"],
        )

    def get(self, request, *args, **kwargs):
        vendor_profile = self.get_object()
        return render(
            request,
            self.template_name,
            {
                "vendor_profile": vendor_profile,
                "has_history": vendor_profile_has_history(vendor_profile),
            },
        )

    def post(self, request, *args, **kwargs):
        vendor_profile = self.get_object()
        result = remove_or_deactivate_vendor_profile(
            profile_id=vendor_profile.pk,
        )

        if result.physically_deleted:
            messages.success(
                request,
                (
                    f"El perfil vendedor de {result.username} fue eliminado "
                    "porque no tenía historia relacionada."
                ),
            )
        else:
            messages.warning(
                request,
                (
                    f"El perfil vendedor de {result.username} conserva "
                    "solicitudes, asignaciones o compras relacionadas y fue "
                    "desactivado sin eliminar su historia."
                ),
            )

        return redirect("vendors:vendorprofile_list")


class ConversionRequestReadOnlyListView(
    AdministratorModeRequiredMixin,
    ListView,
):
    """Listado demostrativo sin edición genérica de estados."""

    model = ConversionRequest
    template_name = "vendors/conversionrequest_list.html"
    context_object_name = "conversion_requests"
    paginate_by = 15
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        queryset = (
            ConversionRequest.objects
            .select_related("client")
            .prefetch_related("assignments__vendor__user")
            .order_by("-created_at", "-id")
        )

        selected_status = self.request.GET.get("status", "").strip()
        valid_statuses = {
            value for value, _ in ConversionRequest.Status.choices
        }
        if selected_status in valid_statuses:
            queryset = queryset.filter(status=selected_status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_status = self.request.GET.get("status", "").strip()
        valid_statuses = {
            value for value, _ in ConversionRequest.Status.choices
        }
        context.update(
            {
                "status_choices": ConversionRequest.Status.choices,
                "selected_status": (
                    selected_status if selected_status in valid_statuses else ""
                ),
            }
        )
        return context


def _client_mode_required(view_func):
    """Exige cuenta operativa, rol CLIENTE y modo CLIENTE."""

    @login_required
    def wrapped(request, *args, **kwargs):
        if not can_use_client_functions(request):
            raise PermissionDenied(
                "Esta operación requiere una cuenta activa en modo CLIENTE."
            )
        return view_func(request, *args, **kwargs)

    return wrapped


def _format_real_minor(amount_minor: int) -> str:
    major, minor = divmod(abs(int(amount_minor)), 100)
    return f"$ {major:,}.{minor:02d}"


@_client_mode_required
@require_GET
def client_conversionrequest_list(request):
    """Lista exclusivamente las solicitudes del Cliente autenticado."""

    queryset = (
        ConversionRequest.objects
        .filter(client=request.user)
        .order_by("-created_at", "-id")
    )
    paginator = Paginator(queryset, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    rows = [
        {
            "request": item,
            "amount_display": _format_real_minor(item.amount_minor),
            "status_label": item.get_status_display(),
        }
        for item in page_obj.object_list
    ]

    return render(
        request,
        "vendors/client_conversionrequest_list.html",
        {
            "request_rows": rows,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
        },
    )


@_client_mode_required
@require_http_methods(["GET", "POST"])
def client_conversionrequest_detail(request, pk):
    """Muestra una solicitud solo cuando pertenece al Cliente actual."""

    conversion_request = get_object_or_404(
        ConversionRequest.objects.prefetch_related(
            "assignments__vendor__user"
        ),
        pk=pk,
        client=request.user,
    )

    if request.method == "POST":
        try:
            cancelled_request, cancelled_now = cancel_conversion_request(
                client=request.user,
                request_id=conversion_request.pk,
            )
            if cancelled_now:
                messages.success(
                    request,
                    "Solicitud cancelada. El REAL reservado volvió a disponible.",
                )
            else:
                messages.info(
                    request,
                    f"La solicitud #{cancelled_request.pk} ya estaba cancelada.",
                )
        except ValidationError as exc:
            message = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
            messages.error(request, message)
        return redirect(
            "vendors:client_conversionrequest_detail",
            pk=conversion_request.pk,
        )

    return render(
        request,
        "vendors/client_conversionrequest_detail.html",
        {
            "conversion_request": conversion_request,
            "amount_display": _format_real_minor(
                conversion_request.amount_minor
            ),
            "can_cancel": (
                conversion_request.status == ConversionRequest.Status.PENDING
                and conversion_request.expires_at > timezone.now()
            ),
        },
    )
