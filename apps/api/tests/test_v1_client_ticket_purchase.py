from __future__ import annotations

import uuid
from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token

from apps.accounts.roles import (
    CLIENT,
    VENDOR,
)
from apps.accounts.tests.factories import create_user
from apps.finance.models import (
    Movement,
    Wallet,
)
from apps.lottery.models import (
    DrawEvent,
    LotteryProduct,
    Ticket,
)


def make_product():
    return LotteryProduct.objects.create(
        code=LotteryProduct.Code.OCTAL,
        name="Octal compra API",
        allowed_symbols="01234567",
        selection_count=4,
        is_active=True,
    )


def make_open_event(product):
    now = timezone.now()

    return DrawEvent.objects.create(
        product=product,
        name="Evento compra API",
        sales_open_at=(
            now
            - timedelta(hours=1)
        ),
        draw_at=(
            now
            + timedelta(hours=2)
        ),
        price_minor=250,
        prize_minor=10000,
        status=DrawEvent.Status.SALES_OPEN,
    )


class ApiV1ClientTicketPurchaseTests(TestCase):
    def setUp(self):
        self.user = create_user(
            username="api_ticket_buyer",
            email="api.ticket.buyer@example.test",
            document="API-TICKET-BUYER",
            roles=(CLIENT,),
        )

        self.product = make_product()

        self.event = make_open_event(
            self.product
        )

        self.wallet = Wallet.objects.get(
            user=self.user,
            currency=Wallet.Currency.VIRTUAL,
        )

        Wallet.objects.filter(
            pk=self.wallet.pk
        ).update(
            available_minor=1000
        )

        self.token = Token.objects.create(
            user=self.user
        )

        self.url = reverse(
            "api:v1-client-ticket-list"
        )

    def _headers(
        self,
        *,
        operation_id=None,
        mode=CLIENT,
    ):
        headers = {
            "HTTP_AUTHORIZATION": (
                f"Token {self.token.key}"
            ),
            "HTTP_X_ACTIVE_MODE": mode,
        }

        if operation_id is not None:
            headers[
                "HTTP_IDEMPOTENCY_KEY"
            ] = str(operation_id)

        return headers

    def _purchase(
        self,
        *,
        operation_id=None,
        event_id=None,
        symbols=None,
        mode=CLIENT,
    ):
        if event_id is None:
            event_id = self.event.pk

        if symbols is None:
            symbols = [
                "0",
                "1",
                "2",
                "3",
            ]

        return self.client.post(
            self.url,
            data={
                "event_id": event_id,
                "symbols": symbols,
            },
            content_type="application/json",
            **self._headers(
                operation_id=operation_id,
                mode=mode,
            ),
        )

    def test_purchase_requires_authentication(self):
        response = self.client.post(
            self.url,
            data={
                "event_id": self.event.pk,
                "symbols": [
                    "0",
                    "1",
                    "2",
                    "3",
                ],
            },
            content_type="application/json",
            HTTP_X_ACTIVE_MODE=CLIENT,
            HTTP_IDEMPOTENCY_KEY=str(
                uuid.uuid4()
            ),
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_purchase_requires_client_mode(self):
        operation_id = uuid.uuid4()

        response = self._purchase(
            operation_id=operation_id,
            mode=VENDOR,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            Ticket.objects.filter(
                operation_id=operation_id
            ).count(),
            0,
        )

    def test_purchase_requires_idempotency_key(self):
        response = self._purchase(
            operation_id=None,
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        payload = response.json()

        self.assertEqual(
            payload["error"]["code"],
            "BAD_REQUEST",
        )

        self.assertIn(
            "idempotency_key",
            payload["error"]["fields"],
        )

        self.assertEqual(
            Ticket.objects.count(),
            0,
        )

    def test_purchase_rejects_invalid_idempotency_key(self):
        response = self.client.post(
            self.url,
            data={
                "event_id": self.event.pk,
                "symbols": [
                    "0",
                    "1",
                    "2",
                    "3",
                ],
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=(
                f"Token {self.token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
            HTTP_IDEMPOTENCY_KEY=(
                "no-es-un-uuid"
            ),
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            Ticket.objects.count(),
            0,
        )

    def test_purchase_creates_ticket_debits_wallet_and_creates_movement(self):
        operation_id = uuid.uuid4()

        response = self._purchase(
            operation_id=operation_id,
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        payload = response.json()

        self.assertTrue(
            payload["created"]
        )

        self.assertEqual(
            payload["ticket"][
                "combination"
            ]["key"],
            "0123",
        )

        ticket = Ticket.objects.get(
            operation_id=operation_id
        )

        self.assertEqual(
            payload["ticket"]["id"],
            ticket.pk,
        )

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.available_minor,
            750,
        )

        movement = Movement.objects.get(
            operation_id=operation_id
        )

        self.assertEqual(
            movement.type,
            Movement.Type.TICKET_PURCHASE,
        )

        self.assertEqual(
            movement.direction,
            Movement.Direction.DEBIT,
        )

        self.assertEqual(
            movement.amount_minor,
            250,
        )

        self.assertEqual(
            movement.balance_after_minor,
            750,
        )

    def test_same_idempotency_key_returns_same_ticket_without_second_debit(self):
        operation_id = uuid.uuid4()

        first = self._purchase(
            operation_id=operation_id,
        )

        second = self._purchase(
            operation_id=operation_id,
        )

        self.assertEqual(
            first.status_code,
            201,
        )

        self.assertEqual(
            second.status_code,
            200,
        )

        self.assertTrue(
            first.json()["created"]
        )

        self.assertFalse(
            second.json()["created"]
        )

        self.assertEqual(
            first.json()["ticket"]["id"],
            second.json()["ticket"]["id"],
        )

        self.assertEqual(
            Ticket.objects.filter(
                operation_id=operation_id
            ).count(),
            1,
        )

        self.assertEqual(
            Movement.objects.filter(
                operation_id=operation_id
            ).count(),
            1,
        )

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.available_minor,
            750,
        )

    def test_same_idempotency_key_with_different_data_is_rejected(self):
        operation_id = uuid.uuid4()

        first = self._purchase(
            operation_id=operation_id,
        )

        self.assertEqual(
            first.status_code,
            201,
        )

        second = self._purchase(
            operation_id=operation_id,
            symbols=[
                "0",
                "1",
                "2",
                "4",
            ],
        )

        self.assertEqual(
            second.status_code,
            400,
        )

        self.assertEqual(
            Ticket.objects.filter(
                operation_id=operation_id
            ).count(),
            1,
        )

        self.assertEqual(
            Movement.objects.filter(
                operation_id=operation_id
            ).count(),
            1,
        )

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.available_minor,
            750,
        )

    def test_invalid_combination_is_normalized_as_api_error(self):
        operation_id = uuid.uuid4()

        response = self._purchase(
            operation_id=operation_id,
            symbols=[
                "0",
                "0",
                "1",
                "2",
            ],
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.json()["error"]["code"],
            "BAD_REQUEST",
        )

        self.assertEqual(
            Ticket.objects.count(),
            0,
        )

        self.assertEqual(
            Movement.objects.filter(
                type=(
                    Movement.Type
                    .TICKET_PURCHASE
                )
            ).count(),
            0,
        )

    def test_insufficient_balance_does_not_create_side_effects(self):
        Wallet.objects.filter(
            pk=self.wallet.pk
        ).update(
            available_minor=100
        )

        operation_id = uuid.uuid4()

        response = self._purchase(
            operation_id=operation_id,
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            Ticket.objects.count(),
            0,
        )

        self.assertEqual(
            Movement.objects.filter(
                operation_id=operation_id
            ).count(),
            0,
        )

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.available_minor,
            100,
        )

    def test_closed_event_is_rejected(self):
        now = timezone.now()

        closed_event = DrawEvent.objects.create(
            product=self.product,
            name="Evento cerrado API",
            sales_open_at=(
                now
                - timedelta(hours=2)
            ),
            draw_at=(
                now
                + timedelta(hours=1)
            ),
            price_minor=250,
            prize_minor=10000,
            status=(
                DrawEvent.Status
                .SALES_CLOSED
            ),
        )

        operation_id = uuid.uuid4()

        response = self._purchase(
            operation_id=operation_id,
            event_id=closed_event.pk,
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            Ticket.objects.filter(
                operation_id=operation_id
            ).count(),
            0,
        )

    def test_missing_event_returns_normalized_404(self):
        operation_id = uuid.uuid4()

        response = self._purchase(
            operation_id=operation_id,
            event_id=999999,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        payload = response.json()

        self.assertEqual(
            payload["error"]["code"],
            "NOT_FOUND",
        )

    def test_custom_multi_character_symbols_are_supported(self):
        custom = LotteryProduct.objects.create(
            kind=LotteryProduct.Kind.CUSTOM,
            code="API_TOKEN_10",
            name="Tokens API",
            allowed_symbols="1|2|10|A",
            selection_count=3,
            is_active=True,
        )

        event = make_open_event(
            custom
        )

        operation_id = uuid.uuid4()

        response = self._purchase(
            operation_id=operation_id,
            event_id=event.pk,
            symbols=[
                "A",
                "10",
                "1",
            ],
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        ticket = Ticket.objects.get(
            operation_id=operation_id
        )

        self.assertEqual(
            ticket.normalized_key,
            "1|10|A",
        )

        self.assertEqual(
            list(ticket.key_tokens),
            [
                "1",
                "10",
                "A",
            ],
        )

        self.assertEqual(
            response.json()["ticket"][
                "combination"
            ]["symbols"],
            [
                "1",
                "10",
                "A",
            ],
        )

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_RENDERER_CLASSES": [
                "rest_framework.renderers.JSONRenderer",
            ],
            "DEFAULT_PARSER_CLASSES": [
                "rest_framework.parsers.JSONParser",
            ],
            "DEFAULT_PERMISSION_CLASSES": [
                "rest_framework.permissions.IsAuthenticated",
            ],
            "DATETIME_FORMAT": "iso-8601",
            "DATE_FORMAT": "iso-8601",
            "EXCEPTION_HANDLER": (
                "apps.api.v1.exceptions."
                "api_exception_handler"
            ),
            "DEFAULT_THROTTLE_RATES": {
                "login": "20/minute",
                "ticket_purchase": "1/minute",
                "vendor_conversion_action": "60/minute",
                "vendor_inventory_purchase": "30/minute",
            },
        }
    )
    
    def test_ticket_purchase_is_throttled(self):
        cache.clear()
        self.addCleanup(cache.clear)

        first_operation_id = uuid.uuid4()
        second_operation_id = uuid.uuid4()

        first = self._purchase(
            operation_id=first_operation_id,
            symbols=[
                "0",
                "1",
                "2",
                "3",
            ],
        )

        self.assertEqual(
            first.status_code,
            201,
        )

        second = self._purchase(
            operation_id=second_operation_id,
            symbols=[
                "0",
                "1",
                "2",
                "4",
            ],
        )

        self.assertEqual(
            second.status_code,
            429,
        )

        payload = second.json()

        self.assertEqual(
            payload["error"]["code"],
            "THROTTLED",
        )

        self.assertEqual(
            Ticket.objects.filter(
                operation_id=first_operation_id
            ).count(),
            1,
        )

        self.assertEqual(
            Ticket.objects.filter(
                operation_id=second_operation_id
            ).count(),
            0,
        )

        self.assertEqual(
            Movement.objects.filter(
                operation_id=first_operation_id
            ).count(),
            1,
        )

        self.assertEqual(
            Movement.objects.filter(
                operation_id=second_operation_id
            ).count(),
            0,
        )

        self.wallet.refresh_from_db()

        self.assertEqual(
            self.wallet.available_minor,
            750,
        )