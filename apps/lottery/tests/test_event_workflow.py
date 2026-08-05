from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.roles import ADMINISTRATOR, CLIENT
from apps.accounts.tests.factories import create_user
from apps.finance.models import Movement, Wallet
from apps.lottery.models import (
    DrawEvent,
    DrawEventStatusTransition,
    LotteryProduct,
    Ticket,
)
from apps.lottery.services import (
    sync_lottery_event_states,
    transition_draw_event,
)


def create_product():
    return LotteryProduct.objects.create(
        code=LotteryProduct.Code.OCTAL,
        name="Octal workflow",
        allowed_symbols="01234567",
        selection_count=4,
        is_active=True,
    )


def create_event(*, product, status=DrawEvent.Status.DRAFT, open_delta=60):
    now = timezone.now()
    return DrawEvent.objects.create(
        product=product,
        name="Evento workflow",
        sales_open_at=now + timedelta(minutes=open_delta),
        draw_at=now + timedelta(hours=3),
        price_minor=250,
        prize_minor=10000,
        status=status,
    )


class EventWorkflowTests(TestCase):
    def setUp(self):
        self.admin = create_user(
            username="workflow_admin",
            email="workflow.admin@example.test",
            document="WORKFLOW-ADMIN",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        self.product = create_product()

    def test_draft_can_be_scheduled_but_cannot_skip_backwards(self):
        event = create_event(product=self.product)
        event, transition, refunded = transition_draw_event(
            event_id=event.pk,
            to_status=DrawEvent.Status.SCHEDULED,
            actor=self.admin,
            reason="Programación inicial.",
            public_message="Abrirá en la fecha indicada.",
        )
        self.assertEqual(event.status, DrawEvent.Status.SCHEDULED)
        self.assertEqual(transition.from_status, DrawEvent.Status.DRAFT)
        self.assertEqual(refunded, 0)

        with self.assertRaises(ValidationError):
            transition_draw_event(
                event_id=event.pk,
                to_status=DrawEvent.Status.DRAFT,
                actor=self.admin,
                reason="Retroceso inválido.",
            )

    def test_scheduled_event_opens_and_closes_by_server_time(self):
        event = create_event(
            product=self.product,
            status=DrawEvent.Status.SCHEDULED,
            open_delta=-5,
        )
        changed = sync_lottery_event_states(now=timezone.now())
        event.refresh_from_db()
        self.assertEqual(changed, 1)
        self.assertEqual(event.status, DrawEvent.Status.SALES_OPEN)

        changed = sync_lottery_event_states(
            now=event.sales_close_at + timedelta(seconds=1)
        )
        event.refresh_from_db()
        self.assertEqual(changed, 1)
        self.assertEqual(event.status, DrawEvent.Status.SALES_CLOSED)

    def test_cancellation_refunds_every_active_ticket_once(self):
        client = create_user(
            username="workflow_client",
            email="workflow.client@example.test",
            document="WORKFLOW-CLIENT",
            roles=(CLIENT,),
        )
        event = create_event(
            product=self.product,
            status=DrawEvent.Status.SALES_OPEN,
            open_delta=-5,
        )
        wallet = Wallet.objects.get(user=client, currency=Wallet.Currency.VIRTUAL)
        Wallet.objects.filter(pk=wallet.pk).update(available_minor=500)
        ticket = Ticket.objects.create(
            user=client,
            event=event,
            normalized_key="0123",
            price_minor=event.price_minor,
        )

        event, _, refunded = transition_draw_event(
            event_id=event.pk,
            to_status=DrawEvent.Status.CANCELLED,
            actor=self.admin,
            reason="Cancelación académica controlada.",
            public_message="El sorteo fue cancelado y los boletos fueron reembolsados.",
        )
        wallet.refresh_from_db()
        ticket.refresh_from_db()
        self.assertEqual(refunded, 1)
        self.assertEqual(wallet.available_minor, 750)
        self.assertEqual(ticket.ownership_status, Ticket.OwnershipStatus.REFUNDED)
        self.assertEqual(ticket.evaluation_status, Ticket.EvaluationStatus.REFUND)
        self.assertEqual(Movement.objects.filter(type=Movement.Type.REFUND).count(), 1)

        with self.assertRaises(ValidationError):
            transition_draw_event(
                event_id=event.pk,
                to_status=DrawEvent.Status.CANCELLED,
                actor=self.admin,
                reason="No duplicar.",
                public_message="No duplicar.",
            )
        self.assertEqual(Movement.objects.filter(type=Movement.Type.REFUND).count(), 1)

    def test_transition_history_is_preserved(self):
        event = create_event(product=self.product)
        transition_draw_event(
            event_id=event.pk,
            to_status=DrawEvent.Status.SCHEDULED,
            actor=self.admin,
            reason="Programación.",
            public_message="Programado.",
        )
        transition = DrawEventStatusTransition.objects.get(event=event)
        self.assertEqual(transition.changed_by, self.admin)
        with self.assertRaises(ValidationError):
            transition.delete()
