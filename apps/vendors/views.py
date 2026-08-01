"""CRUD administrativo y consultas de solo lectura del módulo vendors."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from apps.accounts.access import assigned_mode_codes, get_valid_active_mode
from apps.accounts.models import User
from apps.accounts.roles import ADMINISTRATOR

from .forms import VendorProfileForm
from .models import ConversionRequest, VendorProfile
from .services import (
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
        return (
            VendorProfile.objects
            .select_related("user")
            .prefetch_related(
                "user__groups",
                "assignments__request",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        return (
            VendorProfile.objects
            .select_related("user")
            .get(pk=self.kwargs["pk"])
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
        result = remove_or_deactivate_vendor_profile(
            profile_id=self.kwargs["pk"],
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
