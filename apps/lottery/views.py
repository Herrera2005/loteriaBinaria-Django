"""CRUD Bootstrap administrativo para productos y eventos de lotería."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
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

from .forms import DrawEventForm, LotteryProductForm
from .models import DrawEvent, DrawResult, LotteryProduct
from .services import (
    delete_draw_event,
    delete_lottery_product,
    event_can_be_deleted,
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


class LotteryProductListView(
    AdministratorModeRequiredMixin,
    ListView,
):
    model = LotteryProduct
    template_name = "lottery/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            LotteryProduct.objects
            .annotate(events_count=Count("events"))
            .order_by("id")
        )

        active_filter = self.request.GET.get("active", "").strip()
        if active_filter == "1":
            queryset = queryset.filter(is_active=True)
        elif active_filter == "0":
            queryset = queryset.filter(is_active=False)

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(code__icontains=query)
                | Q(name__icontains=query)
                | Q(allowed_symbols__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_filter = self.request.GET.get("active", "").strip()
        context.update(
            {
                "query": self.request.GET.get("q", "").strip(),
                "active_filter": (
                    active_filter
                    if active_filter in {"", "0", "1"}
                    else ""
                ),
            }
        )
        return context


class LotteryProductDetailView(
    AdministratorModeRequiredMixin,
    DetailView,
):
    model = LotteryProduct
    template_name = "lottery/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return (
            LotteryProduct.objects
            .annotate(events_count=Count("events"))
            .prefetch_related("events")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_delete"] = self.object.events_count == 0
        return context


class LotteryProductCreateView(
    AdministratorModeRequiredMixin,
    CreateView,
):
    model = LotteryProduct
    form_class = LotteryProductForm
    template_name = "lottery/product_form.html"

    def get_success_url(self):
        return reverse(
            "lottery:product_detail",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Producto {self.object.name} creado correctamente.",
        )
        return response


class LotteryProductUpdateView(
    AdministratorModeRequiredMixin,
    UpdateView,
):
    model = LotteryProduct
    form_class = LotteryProductForm
    template_name = "lottery/product_form.html"
    context_object_name = "product"

    def get_success_url(self):
        return reverse(
            "lottery:product_detail",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Producto {self.object.name} actualizado correctamente.",
        )
        return response


class LotteryProductDeleteView(
    AdministratorModeRequiredMixin,
    View,
):
    template_name = "lottery/product_confirm_delete.html"

    def get_object(self):
        return get_object_or_404(
            LotteryProduct.objects.annotate(events_count=Count("events")),
            pk=self.kwargs["pk"],
        )

    def get(self, request, *args, **kwargs):
        return render(
            request,
            self.template_name,
            {"product": self.get_object()},
        )

    def post(self, request, *args, **kwargs):
        product = self.get_object()
        result = delete_lottery_product(product_id=product.pk)

        if result.deleted:
            messages.success(
                request,
                f"Producto {result.label} eliminado correctamente.",
            )
            return redirect("lottery:product_list")

        messages.error(request, result.reason)
        return redirect(
            "lottery:product_detail",
            pk=result.object_id,
        )


class DrawEventListView(
    AdministratorModeRequiredMixin,
    ListView,
):
    model = DrawEvent
    template_name = "lottery/event_list.html"
    context_object_name = "events"
    paginate_by = 15

    def get_queryset(self):
        queryset = (
            DrawEvent.objects
            .select_related("product")
            .annotate(tickets_count=Count("tickets"))
            .order_by("draw_at", "id")
        )

        status = self.request.GET.get("status", "").strip()
        valid_statuses = {value for value, _ in DrawEvent.Status.choices}
        if status in valid_statuses:
            queryset = queryset.filter(status=status)

        product_id = self.request.GET.get("product", "").strip()
        if product_id.isdigit():
            queryset = queryset.filter(product_id=int(product_id))

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(product__name__icontains=query)
                | Q(product__code__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_status = self.request.GET.get("status", "").strip()
        valid_statuses = {value for value, _ in DrawEvent.Status.choices}
        selected_product = self.request.GET.get("product", "").strip()

        context.update(
            {
                "status_choices": DrawEvent.Status.choices,
                "selected_status": (
                    selected_status
                    if selected_status in valid_statuses
                    else ""
                ),
                "products": LotteryProduct.objects.order_by("id"),
                "selected_product": (
                    selected_product
                    if selected_product.isdigit()
                    else ""
                ),
                "query": self.request.GET.get("q", "").strip(),
            }
        )
        return context


class DrawEventDetailView(
    AdministratorModeRequiredMixin,
    DetailView,
):
    model = DrawEvent
    template_name = "lottery/event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return (
            DrawEvent.objects
            .select_related("product")
            .annotate(tickets_count=Count("tickets"))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_delete"] = event_can_be_deleted(self.object)
        try:
            self.object.result
        except DrawResult.DoesNotExist:
            context["has_result"] = False
        else:
            context["has_result"] = True
        return context


class DrawEventCreateView(
    AdministratorModeRequiredMixin,
    CreateView,
):
    model = DrawEvent
    form_class = DrawEventForm
    template_name = "lottery/event_form.html"

    def get_success_url(self):
        return reverse(
            "lottery:event_detail",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Evento {self.object.name} creado correctamente.",
        )
        return response


class DrawEventUpdateView(
    AdministratorModeRequiredMixin,
    UpdateView,
):
    model = DrawEvent
    form_class = DrawEventForm
    template_name = "lottery/event_form.html"
    context_object_name = "event"

    def get_success_url(self):
        return reverse(
            "lottery:event_detail",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Evento {self.object.name} actualizado correctamente.",
        )
        return response


class DrawEventDeleteView(
    AdministratorModeRequiredMixin,
    View,
):
    template_name = "lottery/event_confirm_delete.html"

    def get_object(self):
        return get_object_or_404(
            DrawEvent.objects.select_related("product"),
            pk=self.kwargs["pk"],
        )

    def get(self, request, *args, **kwargs):
        event = self.get_object()
        return render(
            request,
            self.template_name,
            {
                "event": event,
                "can_delete": event_can_be_deleted(event),
            },
        )

    def post(self, request, *args, **kwargs):
        event = self.get_object()
        result = delete_draw_event(event_id=event.pk)

        if result.deleted:
            messages.success(
                request,
                f"Evento {result.label} eliminado correctamente.",
            )
            return redirect("lottery:event_list")

        messages.error(request, result.reason)
        return redirect(
            "lottery:event_detail",
            pk=result.object_id,
        )
