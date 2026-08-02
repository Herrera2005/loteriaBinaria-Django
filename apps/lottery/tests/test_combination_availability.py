"""Pruebas P-35B-R3 para disponibilidad bajo demanda."""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import CLIENT
from apps.accounts.tests.factories import create_user
from apps.finance.models import Wallet
from apps.lottery.availability import get_combination_availability
from apps.lottery.models import DrawEvent, LotteryProduct, Ticket


def make_custom_product():
    return LotteryProduct.objects.create(
        kind=LotteryProduct.Kind.CUSTOM,
        code="R3_TOKENS",
        name="Tokens R3",
        allowed_symbols="1|2|10|A|B",
        selection_count=3,
        is_active=True,
    )


def make_open_event(product):
    now = timezone.now()
    return DrawEvent.objects.create(
        product=product,
        name="Evento disponibilidad",
        sales_open_at=now - timedelta(hours=1),
        draw_at=now + timedelta(hours=2),
        price_minor=100,
        prize_minor=5000,
        status=DrawEvent.Status.SALES_OPEN,
    )


class CombinationAvailabilityTests(TestCase):
    def setUp(self):
        self.user = create_user(
            username="availability_client",
            email="availability@example.test",
            document="AVAILABILITY-CLIENT",
            roles=(CLIENT,),
        )
        self.product = make_custom_product()
        self.event = make_open_event(self.product)

    def create_ticket(self, key):
        return Ticket.objects.create(
            user=self.user,
            event=self.event,
            operation_id=uuid.uuid4(),
            normalized_key=key,
            price_minor=self.event.price_minor,
        )

    def test_partial_count_uses_combinatorics_without_preloading_universe(self):
        result = get_combination_availability(
            event=self.event,
            selected_tokens=("1",),
        )

        self.assertEqual(result.total_matching, 6)
        self.assertEqual(result.sold_matching, 0)
        self.assertEqual(result.available_matching, 6)
        self.assertTrue(result.suggestions)

    def test_sold_permutation_reduces_partial_availability(self):
        self.create_ticket("1|2|10")

        result = get_combination_availability(
            event=self.event,
            selected_tokens=("10", "1"),
        )

        self.assertEqual(result.total_matching, 3)
        self.assertEqual(result.sold_matching, 1)
        self.assertEqual(result.available_matching, 2)
        self.assertNotIn(("1", "2", "10"), result.suggestions)

    def test_complete_sold_combination_has_no_suggestion(self):
        self.create_ticket("1|2|10")

        result = get_combination_availability(
            event=self.event,
            selected_tokens=("10", "2", "1"),
        )

        self.assertEqual(result.total_matching, 1)
        self.assertEqual(result.available_matching, 0)
        self.assertEqual(result.suggestions, ())

    def test_check_view_does_not_buy_or_debit(self):
        wallet = Wallet.objects.get(
            user=self.user,
            currency=Wallet.Currency.VIRTUAL,
        )
        Wallet.objects.filter(pk=wallet.pk).update(available_minor=1000)
        self.client.force_login(self.user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = CLIENT
        session.save()

        response = self.client.post(
            reverse("lottery:client_event_detail", args=(self.event.pk,)),
            {
                "position_1": "1",
                "position_2": "10",
                "position_3": "",
                "operation_id": str(uuid.uuid4()),
                "action": "check_availability",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Disponibilidad de la selección")
        self.assertContains(response, "disponibles")
        self.assertEqual(Ticket.objects.count(), 0)
        wallet.refresh_from_db()
        self.assertEqual(wallet.available_minor, 1000)

    def test_check_rejects_repeated_partial_symbol(self):
        self.client.force_login(self.user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = CLIENT
        session.save()

        response = self.client.post(
            reverse("lottery:client_event_detail", args=(self.event.pk,)),
            {
                "position_1": "1",
                "position_2": "1",
                "position_3": "",
                "operation_id": str(uuid.uuid4()),
                "action": "check_availability",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ya fue seleccionado en otra posición")
        self.assertEqual(Ticket.objects.count(), 0)
