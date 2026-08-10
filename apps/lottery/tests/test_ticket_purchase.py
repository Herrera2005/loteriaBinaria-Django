from __future__ import annotations

import uuid
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import CLIENT, VENDOR
from apps.accounts.tests.factories import create_user
from apps.finance.models import Movement, Wallet
from apps.lottery.models import DrawEvent, LotteryProduct, Ticket
from apps.lottery.services import purchase_ticket


def make_product():
    return LotteryProduct.objects.create(
        code=LotteryProduct.Code.OCTAL,
        name="Octal compra",
        allowed_symbols="01234567",
        selection_count=4,
        is_active=True,
    )


def make_open_event(product):
    now = timezone.now()
    return DrawEvent.objects.create(
        product=product,
        name="Evento compra directa",
        sales_open_at=now - timedelta(hours=1),
        draw_at=now + timedelta(hours=2),
        price_minor=250,
        prize_minor=10000,
        status=DrawEvent.Status.SALES_OPEN,
    )


class TicketPurchaseServiceTests(TestCase):
    def setUp(self):
        self.user = create_user(
            username="ticket_buyer",
            email="ticket.buyer@example.test",
            document="TICKET-BUYER",
            roles=(CLIENT,),
        )
        self.product = make_product()
        self.event = make_open_event(self.product)
        self.wallet = Wallet.objects.get(
            user=self.user,
            currency=Wallet.Currency.VIRTUAL,
        )
        Wallet.objects.filter(pk=self.wallet.pk).update(available_minor=1000)

    def test_purchase_debits_virtual_and_creates_ticket_and_movement(self):
        operation_id = uuid.uuid4()
        ticket, created = purchase_ticket(
            user=self.user,
            active_mode=CLIENT,
            event_id=self.event.pk,
            combination="0123",
            operation_id=operation_id,
        )

        self.assertTrue(created)
        self.assertEqual(ticket.normalized_key, "0123")
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_minor, 750)
        movement = Movement.objects.get(operation_id=operation_id)
        self.assertEqual(movement.type, Movement.Type.TICKET_PURCHASE)
        self.assertEqual(movement.direction, Movement.Direction.DEBIT)
        self.assertEqual(movement.amount_minor, 250)
        self.assertEqual(movement.balance_after_minor, 750)

    def test_same_operation_id_is_idempotent(self):
        operation_id = uuid.uuid4()
        first, first_created = purchase_ticket(
            user=self.user,
            active_mode=CLIENT,
            event_id=self.event.pk,
            combination="0123",
            operation_id=operation_id,
        )
        second, second_created = purchase_ticket(
            user=self.user,
            active_mode=CLIENT,
            event_id=self.event.pk,
            combination="0123",
            operation_id=operation_id,
        )
        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first.pk, second.pk)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_minor, 750)
        self.assertEqual(Movement.objects.filter(operation_id=operation_id).count(), 1)

    def test_same_operation_id_with_other_data_is_rejected(self):
        operation_id = uuid.uuid4()

        first, created = purchase_ticket(
            user=self.user,
            active_mode=CLIENT,
            event_id=self.event.pk,
            combination="0123",
            operation_id=operation_id,
        )

        self.assertTrue(created)
        self.assertEqual(
            first.normalized_key,
            "0123",
        )

        with self.assertRaisesMessage(
            ValidationError,
            "identificador de operación",
        ):
            purchase_ticket(
                user=self.user,
                active_mode=CLIENT,
                event_id=self.event.pk,
                combination="0124",
                operation_id=operation_id,
            )

        self.assertEqual(
            Ticket.objects.filter(
                operation_id=operation_id,
            ).count(),
            1,
        )

        self.assertEqual(
            Movement.objects.filter(
                operation_id=operation_id,
            ).count(),
            1,
        )

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.available_minor,
            750,
        )

    def test_duplicate_combination_is_rejected_without_second_debit(self):
        purchase_ticket(
            user=self.user,
            active_mode=CLIENT,
            event_id=self.event.pk,
            combination="0123",
            operation_id=uuid.uuid4(),
        )
        other = create_user(
            username="other_buyer",
            email="other.buyer@example.test",
            document="OTHER-BUYER",
            roles=(CLIENT,),
        )
        other_wallet = Wallet.objects.get(user=other, currency=Wallet.Currency.VIRTUAL)
        Wallet.objects.filter(pk=other_wallet.pk).update(available_minor=1000)

        with self.assertRaisesMessage(ValidationError, "combinación ya fue comprada"):
            purchase_ticket(
                user=other,
                active_mode=CLIENT,
                event_id=self.event.pk,
                combination="0123",
                operation_id=uuid.uuid4(),
            )
        other_wallet.refresh_from_db()
        self.assertEqual(other_wallet.available_minor, 1000)

    def test_permutation_is_rejected_as_the_same_combination(self):
        purchase_ticket(
            user=self.user,
            active_mode=CLIENT,
            event_id=self.event.pk,
            combination="3210",
            operation_id=uuid.uuid4(),
        )
        other = create_user(
            username="permutation_buyer",
            email="permutation.buyer@example.test",
            document="PERM-BUYER",
            roles=(CLIENT,),
        )
        other_wallet = Wallet.objects.get(
            user=other,
            currency=Wallet.Currency.VIRTUAL,
        )
        Wallet.objects.filter(pk=other_wallet.pk).update(available_minor=1000)

        with self.assertRaisesMessage(ValidationError, "combinación ya fue comprada"):
            purchase_ticket(
                user=other,
                active_mode=CLIENT,
                event_id=self.event.pk,
                combination="0123",
                operation_id=uuid.uuid4(),
            )

        first = Ticket.objects.get(event=self.event)
        self.assertEqual(first.normalized_key, "0123")
        other_wallet.refresh_from_db()
        self.assertEqual(other_wallet.available_minor, 1000)

    def test_invalid_key_and_insufficient_balance_leave_no_effects(self):
        with self.assertRaises(ValidationError):
            purchase_ticket(
                user=self.user,
                active_mode=CLIENT,
                event_id=self.event.pk,
                combination="0012",
                operation_id=uuid.uuid4(),
            )
        Wallet.objects.filter(pk=self.wallet.pk).update(available_minor=100)
        with self.assertRaisesMessage(ValidationError, "Saldo VIRTUAL insuficiente"):
            purchase_ticket(
                user=self.user,
                active_mode=CLIENT,
                event_id=self.event.pk,
                combination="0123",
                operation_id=uuid.uuid4(),
            )
        self.assertEqual(Ticket.objects.count(), 0)
        self.assertEqual(Movement.objects.filter(type=Movement.Type.TICKET_PURCHASE).count(), 0)

    def test_custom_two_character_tokens_are_purchased_by_positions(self):
        custom = LotteryProduct.objects.create(
            kind=LotteryProduct.Kind.CUSTOM,
            code="TOKEN_10",
            name="Tokens de dos caracteres",
            allowed_symbols="1|2|10|A",
            selection_count=3,
            is_active=True,
        )
        event = make_open_event(custom)

        ticket, created = purchase_ticket(
            user=self.user,
            active_mode=CLIENT,
            event_id=event.pk,
            combination=["A", "10", "1"],
            operation_id=uuid.uuid4(),
        )

        self.assertTrue(created)
        self.assertEqual(ticket.normalized_key, "1|10|A")
        self.assertEqual(ticket.key_tokens, ("1", "10", "A"))

    def test_closed_event_is_rejected(self):
        now = timezone.now()
        closed_event = DrawEvent.objects.create(
            product=self.product,
            name="Evento cerrado",
            sales_open_at=now - timedelta(hours=2),
            draw_at=now + timedelta(hours=1),
            price_minor=250,
            prize_minor=10000,
            status=DrawEvent.Status.SALES_CLOSED,
        )
        with self.assertRaisesMessage(ValidationError, "ventas abiertas"):
            purchase_ticket(
                user=self.user,
                active_mode=CLIENT,
                event_id=closed_event.pk,
                combination="0123",
                operation_id=uuid.uuid4(),
            )

    def test_manual_sales_open_allows_purchase_before_planned_opening(self):
        now = timezone.now()

        event = DrawEvent.objects.create(
            product=self.product,
            name="Apertura manual",
            sales_open_at=now + timedelta(hours=2),
            draw_at=now + timedelta(hours=5),
            price_minor=250,
            prize_minor=10000,
            status=DrawEvent.Status.SALES_OPEN,
        )

        Wallet.objects.filter(
            pk=self.wallet.pk,
        ).update(
            available_minor=1000,
        )

        ticket, created = purchase_ticket(
            user=self.user,
            active_mode=CLIENT,
            event_id=event.pk,
            combination="0123",
            operation_id=uuid.uuid4(),
        )

        self.assertTrue(created)
        self.assertEqual(ticket.event_id, event.pk)
        self.assertEqual(ticket.normalized_key, "0123")

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.available_minor,
            750,
        )

        self.assertTrue(
            Movement.objects.filter(
                operation_id=ticket.operation_id,
                type=Movement.Type.TICKET_PURCHASE,
                direction=Movement.Direction.DEBIT,
                amount_minor=250,
            ).exists()
        )


class TicketPurchaseViewTests(TestCase):
    def setUp(self):
        self.user = create_user(
            username="ticket_web",
            email="ticket.web@example.test",
            document="TICKET-WEB",
            roles=(CLIENT,),
        )
        self.vendor = create_user(
            username="ticket_vendor",
            email="ticket.vendor@example.test",
            document="TICKET-VENDOR",
            roles=(VENDOR,),
        )
        self.product = make_product()
        self.event = make_open_event(self.product)
        self.wallet = Wallet.objects.get(user=self.user, currency=Wallet.Currency.VIRTUAL)
        Wallet.objects.filter(pk=self.wallet.pk).update(available_minor=1000)

    def activate(self, user, mode, client=None):
        client = client or self.client
        client.force_login(user)
        session = client.session
        session[ACTIVE_MODE_SESSION_KEY] = mode
        session.save()

    def test_post_buys_ticket_and_redirects_to_own_detail(self):
        self.activate(self.user, CLIENT)
        response = self.client.post(
            reverse("lottery:client_event_detail", kwargs={"pk": self.event.pk}),
            {
                "position_1": "0",
                "position_2": "1",
                "position_3": "2",
                "position_4": "3",
                "operation_id": str(uuid.uuid4()),
            },
        )
        ticket = Ticket.objects.get(user=self.user)
        self.assertRedirects(
            response,
            reverse("lottery:client_ticket_detail", kwargs={"pk": ticket.pk}),
        )

    def test_invalid_symbol_returns_form_error_instead_of_typeerror(self):
        self.activate(self.user, CLIENT)
        response = self.client.post(
            reverse("lottery:client_event_detail", kwargs={"pk": self.event.pk}),
            {
                "position_1": "9",
                "position_2": "1",
                "position_3": "2",
                "position_4": "3",
                "operation_id": str(uuid.uuid4()),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El símbolo seleccionado no está permitido")
        self.assertEqual(Ticket.objects.count(), 0)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_minor, 1000)

    def test_repeated_position_returns_clear_error_without_debit(self):
        self.activate(self.user, CLIENT)
        response = self.client.post(
            reverse("lottery:client_event_detail", kwargs={"pk": self.event.pk}),
            {
                "position_1": "0",
                "position_2": "0",
                "position_3": "2",
                "position_4": "3",
                "operation_id": str(uuid.uuid4()),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ya fue seleccionado en otra posición")
        self.assertEqual(Ticket.objects.count(), 0)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_minor, 1000)

    def test_vendor_mode_cannot_buy(self):
        self.activate(self.vendor, VENDOR)
        response = self.client.post(
            reverse("lottery:client_event_detail", kwargs={"pk": self.event.pk}),
            {"combination": "0123", "operation_id": str(uuid.uuid4())},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_purchase_post_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        self.activate(self.user, CLIENT, csrf_client)
        response = csrf_client.post(
            reverse("lottery:client_event_detail", kwargs={"pk": self.event.pk}),
            {"combination": "0123", "operation_id": str(uuid.uuid4())},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Ticket.objects.count(), 0)
