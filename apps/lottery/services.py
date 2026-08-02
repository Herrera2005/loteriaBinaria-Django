"""Servicios transaccionales del CRUD administrativo de lottery."""
from dataclasses import dataclass
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from .models import DrawEvent, DrawResult, LotteryProduct

@dataclass(frozen=True)
class DeleteResult:
    object_id: int
    label: str
    deleted: bool
    reason: str = ""

@transaction.atomic
def delete_lottery_product(*, product_id: int) -> DeleteResult:
    product = LotteryProduct.objects.select_for_update().get(pk=product_id)
    if product.events.exists():
        return DeleteResult(product.pk, product.name, False, "El producto tiene eventos relacionados y no puede eliminarse.")
    try:
        product.delete()
    except ProtectedError:
        return DeleteResult(product.pk, product.name, False, "El producto conserva relaciones protegidas y no puede eliminarse.")
    return DeleteResult(product_id, product.name, True)

@transaction.atomic
def delete_draw_event(*, event_id: int) -> DeleteResult:
    event = DrawEvent.objects.select_for_update().get(pk=event_id)
    if event.status != DrawEvent.Status.DRAFT:
        return DeleteResult(event.pk, event.name, False, "Solo se puede eliminar un evento en estado Borrador.")
    if event.tickets.exists():
        return DeleteResult(event.pk, event.name, False, "El evento tiene boletos históricos y no puede eliminarse.")
    try:
        event.result
    except DrawResult.DoesNotExist:
        pass
    else:
        return DeleteResult(event.pk, event.name, False, "El evento tiene un resultado histórico y no puede eliminarse.")
    try:
        event.delete()
    except ProtectedError:
        return DeleteResult(event.pk, event.name, False, "El evento conserva relaciones protegidas y no puede eliminarse.")
    return DeleteResult(event_id, event.name, True)

def event_can_be_deleted(event: DrawEvent) -> bool:
    if event.status != DrawEvent.Status.DRAFT or event.tickets.exists():
        return False
    try:
        event.result
    except DrawResult.DoesNotExist:
        return True
    return False


def _assert_active_client(user) -> None:
    from apps.accounts.models import User
    from apps.accounts.roles import CLIENT

    if (
        not getattr(user, "is_active", False)
        or getattr(user, "status", None) != User.Status.ACTIVE
        or not user.groups.filter(name=CLIENT).exists()
    ):
        raise ValidationError("Se requiere una cuenta CLIENTE activa.")


def _active_virtual_wallet(user):
    from apps.finance.models import Wallet

    try:
        wallet = Wallet.objects.select_for_update().get(
            user=user,
            currency=Wallet.Currency.VIRTUAL,
        )
    except Wallet.DoesNotExist as exc:
        raise ValidationError("La wallet VIRTUAL requerida no existe.") from exc

    if wallet.status != Wallet.Status.ACTIVE:
        raise ValidationError("La wallet VIRTUAL no está activa.")
    return wallet


@transaction.atomic
def purchase_ticket(*, user, event_id: int, combination: str, operation_id):
    """Compra directa, atómica e idempotente de un boleto con VIRTUAL."""
    from django.core.exceptions import ValidationError
    from django.db import IntegrityError
    from django.utils import timezone

    from apps.finance.models import Movement

    from .models import Ticket, validate_key_for_product

    _assert_active_client(user)

    event = (
        DrawEvent.objects.select_for_update()
        .select_related("product")
        .get(pk=event_id)
    )
    normalized_key = validate_key_for_product(
        value=combination,
        product=event.product,
        field_name="combination",
    )

    existing = Ticket.objects.filter(operation_id=operation_id).first()
    if existing is not None:
        if (
            existing.user_id != user.pk
            or existing.event_id != event.pk
            or existing.normalized_key != normalized_key
        ):
            raise ValidationError(
                "El identificador de operación ya fue usado con otros datos."
            )
        return existing, False

    now = timezone.now()
    if not event.product.is_active:
        raise ValidationError("El producto del evento no está activo.")
    if event.status != DrawEvent.Status.SALES_OPEN:
        raise ValidationError("El evento no tiene ventas abiertas.")

    if now >= event.sales_close_at:
        raise ValidationError(
            "El periodo de compra de este evento ya terminó."
        )
    
    if Ticket.objects.filter(
        event=event,
        normalized_key=normalized_key,
    ).exists():
        raise ValidationError(
            "La combinación ya fue comprada para este evento."
        )

    wallet = _active_virtual_wallet(user)
    if wallet.available_minor < event.price_minor:
        raise ValidationError("Saldo VIRTUAL insuficiente para comprar el boleto.")

    wallet.available_minor -= event.price_minor
    wallet.save(update_fields=("available_minor", "updated_at"))

    ticket = Ticket(
        user=user,
        event=event,
        operation_id=operation_id,
        normalized_key=normalized_key,
        price_minor=event.price_minor,
    )
    ticket.full_clean()
    try:
        ticket.save(force_insert=True)
    except IntegrityError as exc:
        raise ValidationError(
            "La combinación ya fue comprada para este evento."
        ) from exc

    Movement.objects.create(
        wallet=wallet,
        operation_id=operation_id,
        type=Movement.Type.TICKET_PURCHASE,
        direction=Movement.Direction.DEBIT,
        amount_minor=event.price_minor,
        balance_after_minor=wallet.available_minor,
        description=f"Compra de boleto {normalized_key} para {event.name}.",
    )
    return ticket, True


ALLOWED_EVENT_TRANSITIONS = {
    DrawEvent.Status.DRAFT: {
        DrawEvent.Status.SCHEDULED,
        DrawEvent.Status.CANCELLED,
    },
    DrawEvent.Status.SCHEDULED: {
        DrawEvent.Status.SALES_OPEN,
        DrawEvent.Status.CANCELLED,
    },
    DrawEvent.Status.PUBLISHED: {
        DrawEvent.Status.SALES_OPEN,
        DrawEvent.Status.CANCELLED,
    },
    DrawEvent.Status.SALES_OPEN: {
        DrawEvent.Status.SALES_CLOSED,
        DrawEvent.Status.CANCELLED,
    },
    DrawEvent.Status.SALES_CLOSED: {
        DrawEvent.Status.CANCELLED,
    },
}


def available_event_transitions(event: DrawEvent) -> tuple[str, ...]:
    return tuple(ALLOWED_EVENT_TRANSITIONS.get(event.status, ()))


def _save_event_transition_state(event: DrawEvent, *, fields: tuple[str, ...]) -> None:
    """Persiste una transición validada sin abrir el CRUD genérico de estado."""
    from django.db import models

    models.Model.save(event, update_fields=fields)


@transaction.atomic
def transition_draw_event(
    *,
    event_id: int,
    to_status: str,
    actor,
    reason: str,
    public_message: str = "",
):
    """Avanza un evento por una transición permitida y conserva auditoría."""
    from django.utils import timezone

    from .models import DrawEventStatusTransition

    event = DrawEvent.objects.select_for_update().get(pk=event_id)
    reason = (reason or "").strip()
    public_message = (public_message or "").strip()

    if not reason:
        raise ValidationError("La transición requiere un motivo administrativo.")

    if to_status in (
        DrawEvent.Status.RESULT_SET,
        DrawEvent.Status.FINISHED,
    ):
        raise ValidationError(
            "El resultado y la finalización se procesan exclusivamente "
            "mediante la publicación segura del resultado."
        )

    allowed = ALLOWED_EVENT_TRANSITIONS.get(event.status, set())
    if to_status not in allowed:
        raise ValidationError(
            f"No se permite cambiar de {event.get_status_display()} a {dict(DrawEvent.Status.choices).get(to_status, to_status)}."
        )

    now = timezone.now()
    if to_status == DrawEvent.Status.SCHEDULED:
        if now >= event.sales_close_at:
            raise ValidationError(
                "No se puede programar un evento cuyo cierre de ventas ya pasó."
            )
    elif to_status == DrawEvent.Status.SALES_OPEN:
        if now >= event.sales_close_at:
            raise ValidationError("No se pueden abrir ventas después del cierre.")
    elif to_status == DrawEvent.Status.SALES_CLOSED:
        if event.status != DrawEvent.Status.SALES_OPEN:
            raise ValidationError("Solo un evento con ventas abiertas puede cerrarse.")
    elif to_status == DrawEvent.Status.CANCELLED:
        if not public_message:
            raise ValidationError(
                "La cancelación requiere un mensaje público para los clientes."
            )

    previous_status = event.status
    event.status = to_status
    fields = ["status", "updated_at"]
    if to_status == DrawEvent.Status.CANCELLED:
        event.cancellation_reason = public_message
        fields.append("cancellation_reason")

    _save_event_transition_state(event, fields=tuple(fields))

    transition = DrawEventStatusTransition.objects.create(
        event=event,
        from_status=previous_status,
        to_status=to_status,
        reason=reason,
        public_message=public_message,
        changed_by=actor,
    )

    refunded_count = 0
    if to_status == DrawEvent.Status.CANCELLED:
        refunded_count = refund_cancelled_event_tickets(
            event=event,
            actor=actor,
        )

    return event, transition, refunded_count


@transaction.atomic
def refund_cancelled_event_tickets(*, event: DrawEvent, actor=None) -> int:
    """Reembolsa una vez todos los boletos activos de un evento cancelado."""
    import uuid

    from apps.finance.models import Movement, Wallet
    from .models import Ticket

    if event.status != DrawEvent.Status.CANCELLED:
        raise ValidationError("Solo se reembolsan boletos de un evento cancelado.")

    tickets = list(
        Ticket.objects.select_for_update()
        .select_related("user")
        .filter(
            event=event,
            ownership_status=Ticket.OwnershipStatus.ACTIVE,
        )
        .order_by("id")
    )
    refunded = 0

    for ticket in tickets:
        wallet = Wallet.objects.select_for_update().get(
            user=ticket.user,
            currency=Wallet.Currency.VIRTUAL,
        )
        operation_id = uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"lottery-refund:event:{event.pk}:ticket:{ticket.pk}",
        )

        if Movement.objects.filter(
            wallet=wallet,
            operation_id=operation_id,
            type=Movement.Type.REFUND,
        ).exists():
            continue

        wallet.available_minor += ticket.price_minor
        wallet.save(update_fields=("available_minor", "updated_at"))

        ticket.ownership_status = Ticket.OwnershipStatus.REFUNDED
        ticket.evaluation_status = Ticket.EvaluationStatus.REFUND
        ticket.save(update_fields=("ownership_status", "evaluation_status"))

        Movement.objects.create(
            wallet=wallet,
            operation_id=operation_id,
            type=Movement.Type.REFUND,
            direction=Movement.Direction.CREDIT,
            amount_minor=ticket.price_minor,
            balance_after_minor=wallet.available_minor,
            description=f"Reembolso por cancelación del evento {event.name}.",
        )
        refunded += 1

    return refunded


@transaction.atomic
def sync_lottery_event_states(*, actor=None, now=None) -> int:
    """Abre y cierra ventas por hora del servidor de forma idempotente."""
    from django.utils import timezone
    from .models import DrawEventStatusTransition

    now = now or timezone.now()
    changed = 0

    candidates = list(
        DrawEvent.objects.select_for_update()
        .filter(
            status__in=(
                DrawEvent.Status.SCHEDULED,
                DrawEvent.Status.PUBLISHED,
                DrawEvent.Status.SALES_OPEN,
            )
        )
        .order_by("id")
    )

    for event in candidates:
        target = None
        reason = ""
        public_message = ""

        if (
            event.status in (DrawEvent.Status.SCHEDULED, DrawEvent.Status.PUBLISHED)
            and event.sales_open_at <= now < event.sales_close_at
        ):
            target = DrawEvent.Status.SALES_OPEN
            reason = "Apertura automática por fecha programada."
            public_message = "Las ventas del sorteo ya están abiertas."
        elif event.status == DrawEvent.Status.SALES_OPEN and now >= event.sales_close_at:
            target = DrawEvent.Status.SALES_CLOSED
            reason = "Cierre automático por alcanzar la hora límite."
            public_message = "Las ventas del sorteo han finalizado."

        if target is None:
            continue

        previous = event.status
        event.status = target
        _save_event_transition_state(event, fields=("status", "updated_at"))
        DrawEventStatusTransition.objects.create(
            event=event,
            from_status=previous,
            to_status=target,
            reason=reason,
            public_message=public_message,
            changed_by=actor,
        )
        changed += 1

    return changed


@dataclass(frozen=True)
class ResultPublicationOutcome:
    result: object
    winner_count: int
    refund_count: int
    not_winner_count: int
    credited_count: int


def _result_award_operation_id(ticket_id: int):
    """ID determinista para impedir créditos repetidos del mismo boleto."""
    import uuid

    return uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"lottery-prize:ticket:{ticket_id}",
    )


def _ticket_award_for_result(*, ticket, result):
    """Devuelve estado y monto según coincidencias de símbolos únicos."""
    from .models import Ticket

    ticket_tokens = set(ticket.key_tokens)
    winning_tokens = set(result.key_tokens)
    matching = len(ticket_tokens & winning_tokens)
    required = ticket.event.product.selection_count

    if matching == required:
        return Ticket.EvaluationStatus.WINNER, ticket.event.prize_minor
    if matching == required - 1:
        return Ticket.EvaluationStatus.REFUND, ticket.price_minor
    return Ticket.EvaluationStatus.NOT_WINNER, 0


@transaction.atomic
def settle_draw_result(*, result_id: int) -> ResultPublicationOutcome:
    """Evalúa y acredita cada boleto una sola vez, incluso al reintentar."""
    from django.utils import timezone

    from apps.finance.models import Movement, Wallet
    from .models import DrawEventStatusTransition, Ticket

    result = (
        DrawResult.objects.select_for_update()
        .select_related("event", "event__product")
        .get(pk=result_id)
    )
    event = DrawEvent.objects.select_for_update().get(pk=result.event_id)

    tickets = list(
        Ticket.objects.select_for_update()
        .select_related("event", "event__product", "user")
        .filter(event=event)
        .order_by("user_id", "id")
    )

    user_ids = sorted(
        {
            ticket.user_id
            for ticket in tickets
            if ticket.ownership_status == Ticket.OwnershipStatus.ACTIVE
        }
    )
    wallets = {
        wallet.user_id: wallet
        for wallet in (
            Wallet.objects.select_for_update()
            .filter(
                user_id__in=user_ids,
                currency=Wallet.Currency.VIRTUAL,
            )
            .order_by("user_id", "id")
        )
    }

    winner_count = 0
    refund_count = 0
    not_winner_count = 0
    credited_count = 0
    now = timezone.now()

    for ticket in tickets:
        if ticket.ownership_status != Ticket.OwnershipStatus.ACTIVE:
            continue

        evaluation_status, award_minor = _ticket_award_for_result(
            ticket=ticket,
            result=result,
        )

        if evaluation_status == Ticket.EvaluationStatus.WINNER:
            winner_count += 1
        elif evaluation_status == Ticket.EvaluationStatus.REFUND:
            refund_count += 1
        else:
            not_winner_count += 1

        operation_id = None
        credited_at = ticket.credited_at
        if award_minor > 0:
            operation_id = (
                ticket.award_operation_id
                or _result_award_operation_id(ticket.pk)
            )
            movement_exists = Movement.objects.filter(
                operation_id=operation_id,
                type=Movement.Type.PRIZE,
            ).exists()

            if not movement_exists:
                wallet = wallets.get(ticket.user_id)
                if wallet is None:
                    raise ValidationError(
                        "El ganador no dispone de una billetera VIRTUAL."
                    )
                if wallet.status != Wallet.Status.ACTIVE:
                    raise ValidationError(
                        "La billetera VIRTUAL del ganador no está activa."
                    )

                wallet.available_minor += award_minor
                wallet.save(
                    update_fields=("available_minor", "updated_at")
                )
                Movement.objects.create(
                    wallet=wallet,
                    operation_id=operation_id,
                    type=Movement.Type.PRIZE,
                    direction=Movement.Direction.CREDIT,
                    amount_minor=award_minor,
                    balance_after_minor=wallet.available_minor,
                    description=(
                        f"Premio del evento {event.name} para el boleto "
                        f"{ticket.normalized_key}."
                    ),
                )
                credited_count += 1

            credited_at = credited_at or now

        ticket.evaluation_status = evaluation_status
        ticket.award_minor = award_minor
        ticket.award_operation_id = operation_id
        ticket.credited_at = credited_at
        ticket.save(
            update_fields=(
                "evaluation_status",
                "award_minor",
                "award_operation_id",
                "credited_at",
            )
        )

    if event.status == DrawEvent.Status.RESULT_SET:
        previous_status = event.status
        event.status = DrawEvent.Status.FINISHED
        _save_event_transition_state(
            event,
            fields=("status", "updated_at"),
        )
        DrawEventStatusTransition.objects.create(
            event=event,
            from_status=previous_status,
            to_status=DrawEvent.Status.FINISHED,
            reason="Liquidación automática de boletos completada.",
            public_message="El sorteo finalizó y los premios fueron acreditados.",
            changed_by=result.published_by,
        )

    return ResultPublicationOutcome(
        result=result,
        winner_count=winner_count,
        refund_count=refund_count,
        not_winner_count=not_winner_count,
        credited_count=credited_count,
    )


@transaction.atomic
def publish_draw_result(
    *,
    event_id: int,
    winning_key,
    actor,
    reason: str,
) -> ResultPublicationOutcome:
    """Fija un resultado único, evalúa boletos y finaliza atómicamente."""
    from django.db import IntegrityError
    from django.utils import timezone

    from apps.accounts.policies import has_assigned_role, is_operational_user
    from apps.accounts.roles import ADMINISTRATOR
    from .models import DrawEventStatusTransition

    if not (
        is_operational_user(actor)
        and getattr(actor, "is_staff", False)
        and has_assigned_role(actor, ADMINISTRATOR)
    ):
        raise ValidationError(
            "Solo un Administrador operativo puede publicar resultados."
        )

    event = (
        DrawEvent.objects.select_for_update()
        .select_related("product")
        .get(pk=event_id)
    )
    reason = (reason or "").strip()

    if event.tickets.filter(user=actor).exists():
        raise ValidationError(
            "No puedes publicar el resultado de un evento en el que tienes boleto."
        )
    if not reason:
        raise ValidationError("La publicación requiere un motivo administrativo.")
    if event.status != DrawEvent.Status.SALES_CLOSED:
        raise ValidationError(
            "El resultado solo puede publicarse cuando las ventas están cerradas."
        )
    if timezone.now() < event.draw_at:
        raise ValidationError(
            "El resultado no puede publicarse antes de la hora del sorteo."
        )
    if DrawResult.objects.filter(event=event).exists():
        raise ValidationError(
            "El evento ya tiene un resultado publicado e inmutable."
        )

    result = DrawResult(
        event=event,
        winning_key=winning_key,
        published_by=actor,
        reason=reason,
    )
    result.full_clean()
    try:
        result.save(force_insert=True)
    except IntegrityError as exc:
        raise ValidationError(
            "El evento ya tiene un resultado publicado e inmutable."
        ) from exc

    previous_status = event.status
    event.status = DrawEvent.Status.RESULT_SET
    _save_event_transition_state(
        event,
        fields=("status", "updated_at"),
    )
    DrawEventStatusTransition.objects.create(
        event=event,
        from_status=previous_status,
        to_status=DrawEvent.Status.RESULT_SET,
        reason=reason,
        public_message="El resultado oficial del sorteo fue publicado.",
        changed_by=actor,
    )

    return settle_draw_result(result_id=result.pk)
