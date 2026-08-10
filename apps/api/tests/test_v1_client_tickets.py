from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token

from apps.accounts.roles import (
    CLIENT,
    VENDOR,
)
from apps.lottery.models import (
    DrawEvent,
    LotteryProduct,
    Ticket,
)


User = get_user_model()


class ApiV1ClientTicketTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_group = Group.objects.create(
            name=CLIENT,
        )

        cls.vendor_group = Group.objects.create(
            name=VENDOR,
        )

        cls.client_user = User.objects.create_user(
            username="ticket_client",
            email="ticket.client@example.com",
            password="TicketApi123!",
            first_name="Ticket",
            last_name="Client",
            document="API-TICKET-001",
            birth_date=date(2000, 1, 1),
        )

        cls.client_user.groups.add(
            cls.client_group,
        )

        cls.other_client = User.objects.create_user(
            username="ticket_other",
            email="ticket.other@example.com",
            password="TicketApi123!",
            first_name="Ticket",
            last_name="Other",
            document="API-TICKET-002",
            birth_date=date(2000, 1, 1),
        )

        cls.other_client.groups.add(
            cls.client_group,
        )

        cls.multirole_user = User.objects.create_user(
            username="ticket_multi",
            email="ticket.multi@example.com",
            password="TicketApi123!",
            first_name="Ticket",
            last_name="Multi",
            document="API-TICKET-003",
            birth_date=date(2000, 1, 1),
        )

        cls.multirole_user.groups.add(
            cls.client_group,
            cls.vendor_group,
        )

        cls.octal = LotteryProduct.objects.create(
            kind=LotteryProduct.Kind.OFFICIAL,
            code=LotteryProduct.Code.OCTAL,
            name="Lotería Octal API",
            allowed_symbols="01234567",
            selection_count=4,
            is_active=True,
            accent_color="#F5C542",
        )

        cls.decimal = LotteryProduct.objects.create(
            kind=LotteryProduct.Kind.OFFICIAL,
            code=LotteryProduct.Code.DECIMAL,
            name="Lotería Decimal API",
            allowed_symbols="0123456789",
            selection_count=5,
            is_active=True,
            accent_color="#38BDF8",
        )

        now = timezone.now()

        cls.octal_draw_at = (
            now
            + timedelta(days=1)
        )

        cls.octal_event = DrawEvent.objects.create(
            product=cls.octal,
            name="Octal API #1",
            sales_open_at=(
                now
                - timedelta(hours=1)
            ),
            draw_at=cls.octal_draw_at,
            price_minor=100,
            prize_minor=50000,
            status=DrawEvent.Status.SALES_OPEN,
        )

        cls.decimal_draw_at = (
            now
            + timedelta(days=2)
        )

        cls.decimal_event = DrawEvent.objects.create(
            product=cls.decimal,
            name="Decimal API #1",
            sales_open_at=(
                now
                - timedelta(hours=1)
            ),
            draw_at=cls.decimal_draw_at,
            price_minor=250,
            prize_minor=100000,
            status=DrawEvent.Status.SALES_OPEN,
        )

        cls.pending_ticket = Ticket.objects.create(
            user=cls.client_user,
            event=cls.octal_event,
            operation_id=uuid4(),
            normalized_key="0123",
            price_minor=cls.octal_event.price_minor,
            ownership_status="ACTIVE",
            evaluation_status="PENDING_RESULT",
            award_minor=0,
        )

        cls.winner_ticket = Ticket.objects.create(
            user=cls.client_user,
            event=cls.decimal_event,
            operation_id=uuid4(),
            normalized_key="01234",
            price_minor=cls.decimal_event.price_minor,
            ownership_status="ACTIVE",
            evaluation_status="WINNER",
            award_minor=100000,
            credited_at=now,
            award_operation_id=uuid4(),
        )

        cls.other_ticket = Ticket.objects.create(
            user=cls.other_client,
            event=cls.octal_event,
            operation_id=uuid4(),
            normalized_key="4567",
            price_minor=cls.octal_event.price_minor,
            ownership_status="ACTIVE",
            evaluation_status="PENDING_RESULT",
            award_minor=0,
        )

    @staticmethod
    def _token_for(user):
        return Token.objects.create(
            user=user,
        )

    def test_ticket_list_requires_authentication(self):
        response = self.client.get(
            reverse(
                "api:v1-client-ticket-list"
            )
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_ticket_list_requires_active_mode(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-list"
            ),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_ticket_list_requires_client_mode(self):
        token = self._token_for(
            self.multirole_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-list"
            ),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=VENDOR,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_client_sees_only_own_tickets(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-list"
            ),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["count"],
            2,
        )

        ids = {
            ticket["id"]
            for ticket in payload["results"]
        }

        self.assertEqual(
            ids,
            {
                self.pending_ticket.pk,
                self.winner_ticket.pk,
            },
        )

        self.assertNotIn(
            self.other_ticket.pk,
            ids,
        )

    def test_ticket_detail_returns_stable_contract(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-detail",
                kwargs={
                    "pk": self.pending_ticket.pk,
                },
            ),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            set(payload.keys()),
            {
                "id",
                "event",
                "combination",
                "price",
                "ownership_status",
                "ownership_status_label",
                "evaluation_status",
                "evaluation_status_label",
                "award",
                "credited_at",
                "created_at",
            },
        )

        self.assertEqual(
            payload["id"],
            self.pending_ticket.pk,
        )

        self.assertEqual(
            payload["ownership_status"],
            "ACTIVE",
        )

        self.assertEqual(
            payload["ownership_status_label"],
            "Activo",
        )

        self.assertEqual(
            payload["evaluation_status"],
            "PENDING_RESULT",
        )

        self.assertEqual(
            payload["evaluation_status_label"],
            "Pendiente de resultado",
        )

    def test_ticket_combination_contract_is_correct(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-detail",
                kwargs={
                    "pk": self.pending_ticket.pk,
                },
            ),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["combination"],
            {
                "key": "0123",
                "display": "0 · 1 · 2 · 3",
                "symbols": [
                    "0",
                    "1",
                    "2",
                    "3",
                ],
            },
        )

    def test_ticket_money_contract_uses_minor_units(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-detail",
                kwargs={
                    "pk": self.pending_ticket.pk,
                },
            ),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["price"],
            {
                "minor": 100,
                "display": "V 1.00",
            },
        )

        self.assertEqual(
            payload["award"],
            {
                "minor": 0,
                "display": "V 0.00",
            },
        )

    def test_winner_ticket_exposes_award_and_credit_date(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-detail",
                kwargs={
                    "pk": self.winner_ticket.pk,
                },
            ),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["evaluation_status"],
            "WINNER",
        )

        self.assertEqual(
            payload["evaluation_status_label"],
            "Ganador",
        )

        self.assertEqual(
            payload["award"],
            {
                "minor": 100000,
                "display": "V 1,000.00",
            },
        )

        self.assertIsNotNone(
            payload["credited_at"]
        )

    def test_ticket_event_contract_is_compact(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-detail",
                kwargs={
                    "pk": self.pending_ticket.pk,
                },
            ),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        event = response.json()["event"]

        self.assertEqual(
            set(event.keys()),
            {
                "id",
                "name",
                "status",
                "status_label",
                "draw_at",
                "product",
            },
        )

        self.assertEqual(
            event["id"],
            self.octal_event.pk,
        )

        self.assertEqual(
            event["product"]["code"],
            "OCTAL",
        )

        self.assertEqual(
            set(event["product"].keys()),
            {
                "id",
                "code",
                "name",
                "accent_color",
            },
        )

    def test_ticket_contract_does_not_expose_internal_fields(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-detail",
                kwargs={
                    "pk": self.winner_ticket.pk,
                },
            ),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        forbidden_fields = {
            "user",
            "user_id",
            "operation_id",
            "normalized_key",
            "price_minor",
            "award_minor",
            "award_operation_id",
        }

        for field_name in forbidden_fields:
            with self.subTest(
                field_name=field_name
            ):
                self.assertNotIn(
                    field_name,
                    payload,
                )

    def test_client_cannot_read_another_users_ticket(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-detail",
                kwargs={
                    "pk": self.other_ticket.pk,
                },
            ),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_ticket_list_filters_by_event(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-list"
            ),
            {
                "event": self.octal_event.pk,
            },
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["count"],
            1,
        )

        self.assertEqual(
            payload["results"][0]["id"],
            self.pending_ticket.pk,
        )

    def test_ticket_list_filters_by_product(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-list"
            ),
            {
                "product": self.decimal.pk,
            },
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["count"],
            1,
        )

        self.assertEqual(
            payload["results"][0]["id"],
            self.winner_ticket.pk,
        )

    def test_ticket_list_filters_by_ownership_status_case_insensitively(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-list"
            ),
            {
                "ownership_status": "active",
            },
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["count"],
            2,
        )

    def test_ticket_list_filters_by_evaluation_status_case_insensitively(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-list"
            ),
            {
                "evaluation_status": "winner",
            },
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["count"],
            1,
        )

        self.assertEqual(
            payload["results"][0]["id"],
            self.winner_ticket.pk,
        )

    def test_invalid_ticket_status_filter_does_not_crash(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-list"
            ),
            {
                "evaluation_status": "NO_EXISTE",
            },
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["count"],
            2,
        )

    def test_ticket_list_supports_ordering(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-ticket-list"
            ),
            {
                "ordering": "price_minor",
            },
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.json()["results"]

        self.assertEqual(
            results[0]["id"],
            self.pending_ticket.pk,
        )

        self.assertEqual(
            results[1]["id"],
            self.winner_ticket.pk,
        )


    def test_ticket_detail_is_read_only(self):
        token = self._token_for(
            self.client_user
        )

        url = reverse(
            "api:v1-client-ticket-detail",
            kwargs={
                "pk": self.pending_ticket.pk,
            },
        )

        for method in (
            "put",
            "patch",
            "delete",
        ):
            with self.subTest(
                method=method
            ):
                request_method = getattr(
                    self.client,
                    method,
                )

                response = request_method(
                    url,
                    data={},
                    content_type="application/json",
                    HTTP_AUTHORIZATION=(
                        f"Token {token.key}"
                    ),
                    HTTP_X_ACTIVE_MODE=CLIENT,
                )

                self.assertEqual(
                    response.status_code,
                    405,
                )