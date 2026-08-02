"""CRUD Bootstrap administrativo para productos y eventos de lotería."""

from __future__ import annotations

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Exists, OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from apps.accounts.mixins import (
    ActiveModeRequiredMixin,
    AdministratorModeRequiredMixin,
    EventAdministrationRequiredMixin,
)

from apps.accounts.roles import CLIENT

from .forms import (
    DrawEventForm,
    DrawEventTransitionForm,
    DrawResultPublishForm,
    LotteryProductForm,
    TicketPurchaseForm,
)
from .availability import get_combination_availability
from .models import DrawEvent, DrawResult, LotteryProduct, Ticket
from apps.finance.models import Wallet
from .services import (
    delete_draw_event,
    delete_lottery_product,
    available_event_transitions,
    event_can_be_deleted,
    purchase_ticket,
    publish_draw_result,
    sync_lottery_event_states,
    transition_draw_event,
)


def _add_validation_error(form, exc: ValidationError) -> None:
    """Convierte ValidationError de campo o diccionario en errores de formulario."""
    if hasattr(exc, "message_dict"):
        for field_name, error_messages in exc.message_dict.items():
            target = field_name if field_name in form.fields else None
            for message in error_messages:
                form.add_error(target, message)
        return

    for message in getattr(exc, "messages", (str(exc),)):
        form.add_error(None, message)


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
        sync_lottery_event_states(actor=self.request.user)

        queryset = (
            DrawEvent.objects
            .select_related("product")
            .annotate(
                tickets_count=Count("tickets", distinct=True),
                current_admin_has_ticket=Exists(
                    Ticket.objects.filter(
                        event_id=OuterRef("pk"),
                        user=self.request.user,
                    )
                ),
                current_result_id=Subquery(
                    DrawResult.objects.filter(
                        event_id=OuterRef("pk"),
                    ).values("pk")[:1]
                ),
            )
            .order_by("draw_at", "id")
        )

        status = self.request.GET.get("status", "").strip()
        valid_statuses = {
            value
            for value, _ in DrawEvent.Status.choices
        }

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
    EventAdministrationRequiredMixin,
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
            result = self.object.result
        except DrawResult.DoesNotExist:
            result = None
        context["has_result"] = result is not None
        context["result"] = result
        context["can_publish_result"] = (
            result is None
            and self.object.status == DrawEvent.Status.SALES_CLOSED
            and timezone.now() >= self.object.draw_at
        )
        context["available_transitions"] = available_event_transitions(self.object)
        context["transition_history"] = self.object.status_transitions.select_related("changed_by")[:20]
        context["price_display"] = _format_virtual_minor(self.object.price_minor)
        context["prize_display"] = _format_virtual_minor(self.object.prize_minor)
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
        submit_action = self.request.POST.get("submit_action", "draft")
        if submit_action == "schedule":
            try:
                transition_draw_event(
                    event_id=self.object.pk,
                    to_status=DrawEvent.Status.SCHEDULED,
                    actor=self.request.user,
                    reason="Evento creado y programado por el administrador.",
                    public_message="El sorteo fue programado y abrirá ventas en la fecha indicada.",
                )
                sync_lottery_event_states(actor=self.request.user)
            except ValidationError as exc:
                self.object.delete()
                _add_validation_error(form, exc)
                return self.form_invalid(form)
            messages.success(
                self.request,
                f"Evento {self.object.name} creado y programado correctamente.",
            )
        else:
            messages.success(
                self.request,
                f"Evento {self.object.name} guardado como borrador.",
            )
        return response


class DrawEventUpdateView(
    EventAdministrationRequiredMixin,
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


class DrawEventTransitionView(
    EventAdministrationRequiredMixin,
    View,
):
    template_name = "lottery/event_transition_form.html"

    def get_object(self):
        return get_object_or_404(
            DrawEvent.objects.select_related("product"),
            pk=self.kwargs["pk"],
        )

    def get_target_status(self):
        return self.kwargs["to_status"]

    def get(self, request, *args, **kwargs):
        event = self.get_object()
        target = self.get_target_status()
        if target not in available_event_transitions(event):
            messages.error(request, "La transición solicitada no está permitida.")
            return redirect("lottery:event_detail", pk=event.pk)
        form = DrawEventTransitionForm(
            require_public_message=(target == DrawEvent.Status.CANCELLED),
        )
        return render(request, self.template_name, {
            "event": event,
            "target_status": target,
            "target_label": dict(DrawEvent.Status.choices).get(target, target),
            "form": form,
        })

    def post(self, request, *args, **kwargs):
        event = self.get_object()
        target = self.get_target_status()
        form = DrawEventTransitionForm(
            request.POST,
            require_public_message=(target == DrawEvent.Status.CANCELLED),
        )
        if not form.is_valid():
            return render(request, self.template_name, {
                "event": event,
                "target_status": target,
                "target_label": dict(DrawEvent.Status.choices).get(target, target),
                "form": form,
            })
        try:
            event, _, refunded_count = transition_draw_event(
                event_id=event.pk,
                to_status=target,
                actor=request.user,
                reason=form.cleaned_data["reason"],
                public_message=form.cleaned_data["public_message"],
            )
        except ValidationError as exc:
            _add_validation_error(form, exc)
            return render(request, self.template_name, {
                "event": event,
                "target_status": target,
                "target_label": dict(DrawEvent.Status.choices).get(target, target),
                "form": form,
            })
        if target == DrawEvent.Status.CANCELLED:
            messages.success(
                request,
                f"Evento cancelado. Boletos reembolsados: {refunded_count}.",
            )
        else:
            messages.success(request, f"Estado actualizado a {event.get_status_display()}.")
        return redirect("lottery:event_detail", pk=event.pk)


class DrawResultPublishView(
    EventAdministrationRequiredMixin,
    View,
):
    template_name = "lottery/result_publish_form.html"

    def get_object(self):
        return get_object_or_404(
            DrawEvent.objects.select_related("product"),
            pk=self.kwargs["pk"],
        )

    def _render(self, request, *, event, form, status=200):
        return render(
            request,
            self.template_name,
            {
                "event": event,
                "form": form,
                "prize_display": _format_virtual_minor(event.prize_minor),
            },
            status=status,
        )

    def get(self, request, *args, **kwargs):
        event = self.get_object()
        if event.status != DrawEvent.Status.SALES_CLOSED:
            messages.error(
                request,
                "El resultado solo puede publicarse con ventas cerradas.",
            )
            return redirect("lottery:event_detail", pk=event.pk)
        if timezone.now() < event.draw_at:
            messages.error(
                request,
                "Todavía no ha llegado la hora del sorteo.",
            )
            return redirect("lottery:event_detail", pk=event.pk)
        try:
            event.result
        except DrawResult.DoesNotExist:
            pass
        else:
            messages.error(request, "El evento ya tiene un resultado publicado.")
            return redirect("lottery:event_detail", pk=event.pk)

        return self._render(
            request,
            event=event,
            form=DrawResultPublishForm(event=event),
        )

    def post(self, request, *args, **kwargs):
        event = self.get_object()
        form = DrawResultPublishForm(request.POST, event=event)
        if not form.is_valid():
            return self._render(request, event=event, form=form)

        try:
            outcome = publish_draw_result(
                event_id=event.pk,
                winning_key=form.cleaned_data["winning_key"],
                actor=request.user,
                reason=form.cleaned_data["reason"],
            )
        except ValidationError as exc:
            _add_validation_error(form, exc)
            return self._render(request, event=event, form=form)

        messages.success(
            request,
            (
                "Resultado publicado y sorteo finalizado. "
                f"Ganadores: {outcome.winner_count}; "
                f"devoluciones por cercanía: {outcome.refund_count}; "
                f"no ganadores: {outcome.not_winner_count}."
            ),
        )
        return redirect("lottery:event_detail", pk=event.pk)


class PublicDrawResultDetailView(DetailView):
    model = DrawResult
    template_name = "lottery/public_result_detail.html"
    context_object_name = "result"

    def get_queryset(self):
        return (
            DrawResult.objects
            .select_related("event", "event__product")
            .filter(event__status=DrawEvent.Status.FINISHED)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tickets = self.object.event.tickets.all()
        context.update(
            {
                "winner_count": tickets.filter(
                    evaluation_status=Ticket.EvaluationStatus.WINNER
                ).count(),
                "refund_count": tickets.filter(
                    evaluation_status=Ticket.EvaluationStatus.REFUND
                ).count(),
                "not_winner_count": tickets.filter(
                    evaluation_status=Ticket.EvaluationStatus.NOT_WINNER
                ).count(),
                "ticket_count": tickets.count(),
                "prize_display": _format_virtual_minor(
                    self.object.event.prize_minor
                ),
            }
        )
        return context


class DrawEventDeleteView(
    EventAdministrationRequiredMixin,
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


# Catálogo y boletos propios del modo CLIENTE (P-35A, solo lectura).
def _format_virtual_minor(amount_minor: int) -> str:
    major, minor = divmod(abs(int(amount_minor)), 100)
    sign = "-" if int(amount_minor) < 0 else ""
    return f"{sign}V {major:,}.{minor:02d}"


def _client_visible_events():
    sync_lottery_event_states()
    return (
        DrawEvent.objects
        .filter(
            product__is_active=True,
            status__in=(
                DrawEvent.Status.SCHEDULED,
                DrawEvent.Status.PUBLISHED,
                DrawEvent.Status.SALES_OPEN,
            ),
            sales_close_at__gt=timezone.now(),
        )
        .select_related("product")
        .order_by("draw_at", "id")
    )


class ClientDrawEventListView(ActiveModeRequiredMixin, ListView):
    expected_mode = CLIENT
    model = DrawEvent
    template_name = "lottery/client_event_list.html"
    context_object_name = "events"
    paginate_by = 12

    def get_queryset(self):
        queryset = _client_visible_events()
        product_id = self.request.GET.get("product", "").strip()
        if product_id.isdigit():
            queryset = queryset.filter(product_id=int(product_id))
        availability = self.request.GET.get("availability", "").strip()
        now = timezone.now()
        if availability == "open":
            queryset = queryset.filter(
                status=DrawEvent.Status.SALES_OPEN,
                sales_close_at__gt=now,
            )
        elif availability == "upcoming":
            queryset = queryset.filter(
                status__in=(
                    DrawEvent.Status.SCHEDULED,
                    DrawEvent.Status.PUBLISHED,
                ),
                sales_open_at__gt=now,
            )
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
        now = timezone.now()
        context["event_rows"] = [
            {
                "event": event,
                "price_display": _format_virtual_minor(event.price_minor),
                "prize_display": _format_virtual_minor(event.prize_minor),
                "is_open_now": (
                    event.status == DrawEvent.Status.SALES_OPEN
                    and now < event.sales_close_at
                ),
                "is_upcoming": (
                    event.status in (
                        DrawEvent.Status.SCHEDULED,
                        DrawEvent.Status.PUBLISHED,
                    )
                    and event.sales_open_at > now
                ),
            }
            for event in context["events"]
        ]
        selected_product = self.request.GET.get("product", "").strip()
        availability = self.request.GET.get("availability", "").strip()
        context.update({
            "products": LotteryProduct.objects.filter(is_active=True).order_by("id"),
            "selected_product": selected_product if selected_product.isdigit() else "",
            "selected_availability": availability if availability in {"", "open", "upcoming"} else "",
            "query": self.request.GET.get("q", "").strip(),
        })
        return context


class ClientDrawEventDetailView(ActiveModeRequiredMixin, DetailView):
    def dispatch(self, request, *args, **kwargs):
        sync_lottery_event_states()
        return super().dispatch(request, *args, **kwargs)

    expected_mode = CLIENT
    model = DrawEvent
    template_name = "lottery/client_event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return _client_visible_events()

    def _virtual_wallet(self):
        return Wallet.objects.filter(
            user=self.request.user,
            currency=Wallet.Currency.VIRTUAL,
        ).first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        wallet = self._virtual_wallet()
        purchase_form = kwargs.get("purchase_form")
        if purchase_form is None:
            purchase_form = TicketPurchaseForm(event=self.object)
        availability_result = kwargs.get("availability_result")
        latest_transition = self.object.status_transitions.exclude(public_message="").first()
        context.update({
            "public_status_message": latest_transition.public_message if latest_transition else self.object.cancellation_reason,
            "price_display": _format_virtual_minor(self.object.price_minor),
            "prize_display": _format_virtual_minor(self.object.prize_minor),
            "is_open_now": (
                self.object.status == DrawEvent.Status.SALES_OPEN
                and now < self.object.sales_close_at
            ),
            "is_upcoming": (
                self.object.status in (
                    DrawEvent.Status.SCHEDULED,
                    DrawEvent.Status.PUBLISHED,
                )
                and self.object.sales_open_at > now
            ),
            "purchase_form": purchase_form,
            "availability_result": availability_result,
            "virtual_available_display": _format_virtual_minor(
                wallet.available_minor if wallet else 0
            ),
            "balance_after_display": _format_virtual_minor(
                max((wallet.available_minor if wallet else 0) - self.object.price_minor, 0)
            ),
            "has_enough_virtual": bool(
                wallet
                and wallet.status == Wallet.Status.ACTIVE
                and wallet.available_minor >= self.object.price_minor
            ),
        })
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("action", "buy")
        is_availability_check = action == "check_availability"
        form = TicketPurchaseForm(
            request.POST,
            event=self.object,
            require_complete=not is_availability_check,
        )

        if form.is_valid() and is_availability_check:
            try:
                availability_result = get_combination_availability(
                    event=self.object,
                    selected_tokens=form.selected_tokens,
                )
            except ValidationError as exc:
                _add_validation_error(form, exc)
            else:
                context = self.get_context_data(
                    purchase_form=form,
                    availability_result=availability_result,
                )
                return self.render_to_response(context)

        if form.is_valid():
            try:
                ticket, created = purchase_ticket(
                    user=request.user,
                    event_id=self.object.pk,
                    combination=form.cleaned_data["combination"],
                    operation_id=form.cleaned_data["operation_id"],
                )
            except ValidationError as exc:
                _add_validation_error(form, exc)
            else:
                if created:
                    messages.success(
                        request,
                        "Boleto comprado correctamente con saldo VIRTUAL.",
                    )
                else:
                    messages.info(
                        request,
                        "La compra ya había sido confirmada anteriormente.",
                    )
                return redirect(
                    "lottery:client_ticket_detail",
                    pk=ticket.pk,
                )

        context = self.get_context_data(purchase_form=form)
        return self.render_to_response(context)


class ClientTicketListView(ActiveModeRequiredMixin, ListView):
    expected_mode = CLIENT
    model = Ticket
    template_name = "lottery/client_ticket_list.html"
    context_object_name = "tickets"
    paginate_by = 15

    def get_queryset(self):
        queryset = (Ticket.objects.filter(user=self.request.user)
                    .select_related("event", "event__product")
                    .order_by("-created_at", "-id"))
        product_id = self.request.GET.get("product", "").strip()
        if product_id.isdigit():
            queryset = queryset.filter(event__product_id=int(product_id))
        status = self.request.GET.get("status", "").strip()
        valid_statuses = {value for value, _ in Ticket.OwnershipStatus.choices}
        if status in valid_statuses:
            queryset = queryset.filter(ownership_status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ticket_rows"] = [
            {
                "ticket": ticket,
                "price_display": _format_virtual_minor(ticket.price_minor),
                "award_display": _format_virtual_minor(ticket.award_minor),
            }
            for ticket in context["tickets"]
        ]
        selected_product = self.request.GET.get("product", "").strip()
        selected_status = self.request.GET.get("status", "").strip()
        valid_statuses = {value for value, _ in Ticket.OwnershipStatus.choices}
        context.update({
            "products": LotteryProduct.objects.filter(is_active=True).order_by("id"),
            "ownership_choices": Ticket.OwnershipStatus.choices,
            "selected_product": selected_product if selected_product.isdigit() else "",
            "selected_status": selected_status if selected_status in valid_statuses else "",
        })
        return context


class ClientTicketDetailView(ActiveModeRequiredMixin, DetailView):
    expected_mode = CLIENT
    model = Ticket
    template_name = "lottery/client_ticket_detail.html"
    context_object_name = "ticket"

    def get_queryset(self):
        return (Ticket.objects.filter(user=self.request.user)
                .select_related("event", "event__product", "event__result"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event = self.object.event

        latest_transition = (
            event.status_transitions
            .exclude(public_message="")
            .first()
        )

        context.update(
            {
                "ticket": self.object,
                "event": event,
            "public_status_message": (
                    latest_transition.public_message
                    if latest_transition
                    else event.cancellation_reason
                ),
            }
        )

        return context