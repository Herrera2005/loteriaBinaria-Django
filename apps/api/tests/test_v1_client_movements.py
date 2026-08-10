from __future__ import annotations

import uuid

from django.test import TestCase
from django.urls import reverse
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


class ApiV1ClientMovementTests(TestCase):
    def setUp(self):
        self.user = create_user(
            username="movement_client",
            email="movement.client@example.test",
            document="MOVEMENT-CLIENT",
            roles=(CLIENT,),
        )

        self.other_user = create_user(
            username="movement_other",
            email="movement.other@example.test",
            document="MOVEMENT-OTHER",
            roles=(CLIENT,),
        )

        self.multirole_user = create_user(
            username="movement_multi",
            email="movement.multi@example.test",
            document="MOVEMENT-MULTI",
            roles=(
                CLIENT,
                VENDOR,
            ),
        )

        self.real_wallet = Wallet.objects.get(
            user=self.user,
            currency=Wallet.Currency.REAL,
        )

        self.virtual_wallet = Wallet.objects.get(
            user=self.user,
            currency=Wallet.Currency.VIRTUAL,
        )

        self.other_wallet = Wallet.objects.get(
            user=self.other_user,
            currency=Wallet.Currency.VIRTUAL,
        )

        self.top_up = Movement.objects.create(
            wallet=self.real_wallet,
            operation_id=uuid.uuid4(),
            type=Movement.Type.TOP_UP,
            direction=Movement.Direction.CREDIT,
            amount_minor=10000,
            balance_after_minor=10000,
            description="Recarga de prueba.",
        )

        self.ticket_purchase = Movement.objects.create(
            wallet=self.virtual_wallet,
            operation_id=uuid.uuid4(),
            type=Movement.Type.TICKET_PURCHASE,
            direction=Movement.Direction.DEBIT,
            amount_minor=250,
            balance_after_minor=750,
            description="Compra de boleto de prueba.",
        )

        self.prize = Movement.objects.create(
            wallet=self.virtual_wallet,
            operation_id=uuid.uuid4(),
            type=Movement.Type.PRIZE,
            direction=Movement.Direction.CREDIT,
            amount_minor=5000,
            balance_after_minor=5750,
            description="Premio de prueba.",
        )

        self.other_movement = Movement.objects.create(
            wallet=self.other_wallet,
            operation_id=uuid.uuid4(),
            type=Movement.Type.TOP_UP,
            direction=Movement.Direction.CREDIT,
            amount_minor=999999,
            balance_after_minor=999999,
            description="Movimiento ajeno.",
        )

        self.token = Token.objects.create(
            user=self.user,
        )

        self.multirole_token = Token.objects.create(
            user=self.multirole_user,
        )

        self.list_url = reverse(
            "api:v1-client-movement-list"
        )

    def _headers(
        self,
        *,
        mode=CLIENT,
    ):
        return {
            "HTTP_AUTHORIZATION": (
                f"Token {self.token.key}"
            ),
            "HTTP_X_ACTIVE_MODE": mode,
        }

    def test_movement_list_requires_authentication(self):
        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_movement_list_requires_active_mode(self):
        response = self.client.get(
            self.list_url,
            HTTP_AUTHORIZATION=(
                f"Token {self.token.key}"
            ),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_movement_list_requires_client_mode(self):
        response = self.client.get(
            self.list_url,
            HTTP_AUTHORIZATION=(
                f"Token {self.multirole_token.key}"
            ),
            HTTP_X_ACTIVE_MODE=VENDOR,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_client_sees_only_own_movements(self):
        response = self.client.get(
            self.list_url,
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["count"],
            3,
        )

        ids = {
            movement["id"]
            for movement in payload["results"]
        }

        self.assertEqual(
            ids,
            {
                self.top_up.pk,
                self.ticket_purchase.pk,
                self.prize.pk,
            },
        )

        self.assertNotIn(
            self.other_movement.pk,
            ids,
        )

    def test_movement_detail_returns_expected_contract(self):
        response = self.client.get(
            reverse(
                "api:v1-client-movement-detail",
                kwargs={
                    "pk": self.ticket_purchase.pk,
                },
            ),
            **self._headers(),
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
                "wallet",
                "type",
                "type_label",
                "direction",
                "direction_label",
                "amount",
                "balance_after",
                "description",
                "created_at",
            },
        )

        self.assertEqual(
            payload["type"],
            Movement.Type.TICKET_PURCHASE,
        )

        self.assertEqual(
            payload["type_label"],
            "Compra de boleto",
        )

        self.assertEqual(
            payload["direction"],
            Movement.Direction.DEBIT,
        )

        self.assertEqual(
            payload["direction_label"],
            "Débito",
        )

    def test_movement_money_contract_uses_minor_units(self):
        response = self.client.get(
            reverse(
                "api:v1-client-movement-detail",
                kwargs={
                    "pk": self.ticket_purchase.pk,
                },
            ),
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["amount"],
            {
                "minor": 250,
                "currency": "VIRTUAL",
                "display": "V 2.50",
            },
        )

        self.assertEqual(
            payload["balance_after"],
            {
                "minor": 750,
                "currency": "VIRTUAL",
                "display": "V 7.50",
            },
        )

    def test_movement_wallet_contract_is_compact(self):
        response = self.client.get(
            reverse(
                "api:v1-client-movement-detail",
                kwargs={
                    "pk": self.ticket_purchase.pk,
                },
            ),
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        wallet = response.json()["wallet"]

        self.assertEqual(
            set(wallet.keys()),
            {
                "id",
                "currency",
                "currency_label",
            },
        )

        self.assertEqual(
            wallet["id"],
            self.virtual_wallet.pk,
        )

        self.assertEqual(
            wallet["currency"],
            Wallet.Currency.VIRTUAL,
        )

    def test_movement_does_not_expose_operation_id(self):
        response = self.client.get(
            reverse(
                "api:v1-client-movement-detail",
                kwargs={
                    "pk": self.ticket_purchase.pk,
                },
            ),
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertNotIn(
            "operation_id",
            payload,
        )

        self.assertNotIn(
            "wallet_id",
            payload,
        )

        self.assertNotIn(
            "amount_minor",
            payload,
        )

        self.assertNotIn(
            "balance_after_minor",
            payload,
        )

    def test_client_cannot_read_another_users_movement(self):
        response = self.client.get(
            reverse(
                "api:v1-client-movement-detail",
                kwargs={
                    "pk": self.other_movement.pk,
                },
            ),
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_movement_list_filters_by_currency(self):
        response = self.client.get(
            self.list_url,
            {
                "currency": "virtual",
            },
            **self._headers(),
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

        for movement in payload["results"]:
            self.assertEqual(
                movement["wallet"]["currency"],
                Wallet.Currency.VIRTUAL,
            )

    def test_movement_list_filters_by_type(self):
        response = self.client.get(
            self.list_url,
            {
                "type": "ticket_purchase",
            },
            **self._headers(),
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
            self.ticket_purchase.pk,
        )

    def test_movement_list_filters_by_direction(self):
        response = self.client.get(
            self.list_url,
            {
                "direction": "credit",
            },
            **self._headers(),
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

        for movement in payload["results"]:
            self.assertEqual(
                movement["direction"],
                Movement.Direction.CREDIT,
            )

    def test_invalid_filter_returns_bad_request(self):
        response = self.client.get(
            self.list_url,
            {
                "type": "NO_EXISTE",
            },
            **self._headers(),
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
            "type",
            payload["error"]["fields"],
        )

    def test_movement_list_supports_ordering(self):
        response = self.client.get(
            self.list_url,
            {
                "ordering": "amount_minor",
            },
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        amounts = [
            movement["amount"]["minor"]
            for movement
            in response.json()["results"]
        ]

        self.assertEqual(
            amounts,
            sorted(amounts),
        )

    def test_movement_collection_is_read_only(self):
        response = self.client.post(
            self.list_url,
            data={
                "type": "TOP_UP",
            },
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_movement_detail_is_read_only(self):
        url = reverse(
            "api:v1-client-movement-detail",
            kwargs={
                "pk": self.ticket_purchase.pk,
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
                    **self._headers(),
                )

                self.assertEqual(
                    response.status_code,
                    405,
                )

    def test_invalid_ordering_returns_bad_request(self):
        response = self.client.get(
            self.list_url,
            {
                "ordering": "pepito",
            },
            **self._headers(),
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
            "ordering",
            payload["error"]["fields"],
        )

    def test_valid_ordering_is_accepted(self):
        response = self.client.get(
            self.list_url,
            {
                "ordering": "-created_at",
            },
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )