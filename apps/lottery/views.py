"""CRUD Bootstrap administrativo para productos y eventos de lotería."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View
from apps.accounts.access import assigned_mode_codes, get_valid_active_mode
from apps.accounts.models import User
from apps.accounts.roles import ADMINISTRATOR
from .forms import DrawEventForm, LotteryProductForm
from .models import DrawEvent, LotteryProduct
from .services import delete_draw_event, delete_lottery_product, event_can_be_deleted

class AdministratorModeRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True
    def test_func(self):
        user = self.request.user
        return (user.is_authenticated and user.is_active and user.status == User.Status.ACTIVE and user.is_staff and ADMINISTRATOR in assigned_mode_codes(user) and get_valid_active_mode(self.request) == ADMINISTRATOR)
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
        raise PermissionDenied("Se requiere una cuenta administrativa activa y el modo ADMINISTRADOR.")

class LotteryProductListView(AdministratorModeRequiredMixin, ListView):
    model = LotteryProduct; template_name = "lottery/product_list.html"; context_object_name = "products"; paginate_by = 12
    def get_queryset(self):
        qs = LotteryProduct.objects.annotate(events_count=Count("events")).order_by("id")
        active = self.request.GET.get("active", "").strip()
        if active == "1": qs = qs.filter(is_active=True)
        elif active == "0": qs = qs.filter(is_active=False)
        q = self.request.GET.get("q", "").strip()
        if q: qs = qs.filter(Q(code__icontains=q)|Q(name__icontains=q)|Q(allowed_symbols__icontains=q))
        return qs
    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs); active = self.request.GET.get("active", "").strip()
        c.update({"query": self.request.GET.get("q", "").strip(), "active_filter": active if active in {"", "0", "1"} else ""}); return c

class LotteryProductDetailView(AdministratorModeRequiredMixin, DetailView):
    model = LotteryProduct; template_name = "lottery/product_detail.html"; context_object_name = "product"
    def get_queryset(self): return LotteryProduct.objects.prefetch_related("events")
class LotteryProductCreateView(AdministratorModeRequiredMixin, CreateView):
    model = LotteryProduct; form_class = LotteryProductForm; template_name = "lottery/product_form.html"
    def get_success_url(self): return reverse("lottery:product_detail", kwargs={"pk": self.object.pk})
    def form_valid(self, form):
        r = super().form_valid(form); messages.success(self.request, f"Producto {self.object.name} creado correctamente."); return r
class LotteryProductUpdateView(AdministratorModeRequiredMixin, UpdateView):
    model = LotteryProduct; form_class = LotteryProductForm; template_name = "lottery/product_form.html"; context_object_name = "product"
    def get_success_url(self): return reverse("lottery:product_detail", kwargs={"pk": self.object.pk})
    def form_valid(self, form):
        r = super().form_valid(form); messages.success(self.request, f"Producto {self.object.name} actualizado correctamente."); return r
class LotteryProductDeleteView(AdministratorModeRequiredMixin, View):
    template_name = "lottery/product_confirm_delete.html"
    def get_object(self): return LotteryProduct.objects.annotate(events_count=Count("events")).get(pk=self.kwargs["pk"])
    def get(self, request, *args, **kwargs): return render(request, self.template_name, {"product": self.get_object()})
    def post(self, request, *args, **kwargs):
        result = delete_lottery_product(product_id=self.kwargs["pk"])
        if result.deleted:
            messages.success(request, f"Producto {result.label} eliminado correctamente."); return redirect("lottery:product_list")
        messages.error(request, result.reason); return redirect("lottery:product_detail", pk=result.object_id)

class DrawEventListView(AdministratorModeRequiredMixin, ListView):
    model = DrawEvent; template_name = "lottery/event_list.html"; context_object_name = "events"; paginate_by = 15
    def get_queryset(self):
        qs = DrawEvent.objects.select_related("product").annotate(tickets_count=Count("tickets")).order_by("draw_at", "id")
        status = self.request.GET.get("status", "").strip(); valid = {v for v,_ in DrawEvent.Status.choices}
        if status in valid: qs = qs.filter(status=status)
        product = self.request.GET.get("product", "").strip()
        if product.isdigit(): qs = qs.filter(product_id=int(product))
        q = self.request.GET.get("q", "").strip()
        if q: qs = qs.filter(Q(name__icontains=q)|Q(product__name__icontains=q)|Q(product__code__icontains=q))
        return qs
    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs); status = self.request.GET.get("status", "").strip(); valid = {v for v,_ in DrawEvent.Status.choices}; product = self.request.GET.get("product", "").strip()
        c.update({"status_choices": DrawEvent.Status.choices, "selected_status": status if status in valid else "", "products": LotteryProduct.objects.order_by("id"), "selected_product": product if product.isdigit() else "", "query": self.request.GET.get("q", "").strip()}); return c

class DrawEventDetailView(AdministratorModeRequiredMixin, DetailView):
    model = DrawEvent; template_name = "lottery/event_detail.html"; context_object_name = "event"
    def get_queryset(self): return DrawEvent.objects.select_related("product").prefetch_related("tickets")
    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs); c["can_delete"] = event_can_be_deleted(self.object); return c
class DrawEventCreateView(AdministratorModeRequiredMixin, CreateView):
    model = DrawEvent; form_class = DrawEventForm; template_name = "lottery/event_form.html"
    def get_success_url(self): return reverse("lottery:event_detail", kwargs={"pk": self.object.pk})
    def form_valid(self, form):
        r = super().form_valid(form); messages.success(self.request, f"Evento {self.object.name} creado correctamente."); return r
class DrawEventUpdateView(AdministratorModeRequiredMixin, UpdateView):
    model = DrawEvent; form_class = DrawEventForm; template_name = "lottery/event_form.html"; context_object_name = "event"
    def get_success_url(self): return reverse("lottery:event_detail", kwargs={"pk": self.object.pk})
    def form_valid(self, form):
        r = super().form_valid(form); messages.success(self.request, f"Evento {self.object.name} actualizado correctamente."); return r
class DrawEventDeleteView(AdministratorModeRequiredMixin, View):
    template_name = "lottery/event_confirm_delete.html"
    def get_object(self): return DrawEvent.objects.select_related("product").get(pk=self.kwargs["pk"])
    def get(self, request, *args, **kwargs):
        event = self.get_object(); return render(request, self.template_name, {"event": event, "can_delete": event_can_be_deleted(event)})
    def post(self, request, *args, **kwargs):
        result = delete_draw_event(event_id=self.kwargs["pk"])
        if result.deleted:
            messages.success(request, f"Evento {result.label} eliminado correctamente."); return redirect("lottery:event_list")
        messages.error(request, result.reason); return redirect("lottery:event_detail", pk=result.object_id)
