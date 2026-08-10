from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from apps.accounts.roles import (
    CLIENT,
    VENDOR,
)
from apps.finance.models import Wallet


User = get_user_model()


class ApiV1ClientWalletTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_group = Group.objects.create(
            name=CLIENT,
        )

        cls.vendor_group = Group.objects.create(
            name=VENDOR,
        )

        cls.client_user = User.objects.create_user(
            username="wallet_client",
            email="wallet.client@example.com",
            password="WalletApi123!",
            first_name="Wallet",
            last_name="Client",
            document="API-WALLET-001",
            birth_date=date(2000, 1, 1),
        )

        cls.client_user.groups.add(
            cls.client_group,
        )

        cls.other_client = User.objects.create_user(
            username="wallet_other",
            email="wallet.other@example.com",
            password="WalletApi123!",
            first_name="Wallet",
            last_name="Other",
            document="API-WALLET-002",
            birth_date=date(2000, 1, 1),
        )

        cls.other_client.groups.add(
            cls.client_group,
        )

        cls.multirole_user = User.objects.create_user(
            username="wallet_multi",
            email="wallet.multi@example.com",
            password="WalletApi123!",
            first_name="Wallet",
            last_name="Multi",
            document="API-WALLET-003",
            birth_date=date(2000, 1, 1),
        )

        cls.multirole_user.groups.add(
            cls.client_group,
            cls.vendor_group,
        )

        # Las wallets ya son provisionadas por el dominio al crear el usuario.
        # No debemos crear duplicados REAL/VIRTUAL en las pruebas.

        cls.real_wallet = Wallet.objects.get(
            user=cls.client_user,
            currency=Wallet.Currency.REAL,
        )

        cls.real_wallet.available_minor = 12500
        cls.real_wallet.reserved_minor = 2500
        cls.real_wallet.status = Wallet.Status.ACTIVE
        cls.real_wallet.save(
            update_fields=[
                "available_minor",
                "reserved_minor",
                "status",
                "updated_at",
            ]
        )

        cls.virtual_wallet = Wallet.objects.get(
            user=cls.client_user,
            currency=Wallet.Currency.VIRTUAL,
        )

        cls.virtual_wallet.available_minor = 5000
        cls.virtual_wallet.reserved_minor = 0
        cls.virtual_wallet.status = Wallet.Status.ACTIVE
        cls.virtual_wallet.save(
            update_fields=[
                "available_minor",
                "reserved_minor",
                "status",
                "updated_at",
            ]
        )

        cls.other_wallet = Wallet.objects.get(
            user=cls.other_client,
            currency=Wallet.Currency.REAL,
        )

        cls.other_wallet.available_minor = 999999
        cls.other_wallet.reserved_minor = 0
        cls.other_wallet.status = Wallet.Status.ACTIVE
        cls.other_wallet.save(
            update_fields=[
                "available_minor",
                "reserved_minor",
                "status",
                "updated_at",
            ]
        )

    @staticmethod
    def _token_for(user):
        return Token.objects.create(
            user=user,
        )

    def test_wallet_list_requires_authentication(self):
        response = self.client.get(
            reverse(
                "api:v1-client-wallet-list"
            )
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_wallet_list_requires_active_mode(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-wallet-list"
            ),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_wallet_list_requires_client_mode(self):
        token = self._token_for(
            self.multirole_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-wallet-list"
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

    def test_client_sees_only_own_wallets(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-wallet-list"
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
            len(payload),
            2,
        )

        ids = {
            wallet["id"]
            for wallet in payload
        }

        self.assertEqual(
            ids,
            {
                self.real_wallet.pk,
                self.virtual_wallet.pk,
            },
        )

        self.assertNotIn(
            self.other_wallet.pk,
            ids,
        )

    def test_wallet_contract_uses_minor_units(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-wallet-detail",
                kwargs={
                    "pk": self.real_wallet.pk,
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
            payload["currency"],
            Wallet.Currency.REAL,
        )

        self.assertEqual(
            payload["status"],
            Wallet.Status.ACTIVE,
        )

        self.assertEqual(
            payload["available"],
            {
                "minor": 12500,
                "display": "V 125.00",
            },
        )

        self.assertEqual(
            payload["reserved"],
            {
                "minor": 2500,
                "display": "V 25.00",
            },
        )

        self.assertEqual(
            payload["total"],
            {
                "minor": 15000,
                "display": "V 150.00",
            },
        )

    def test_wallet_contract_does_not_expose_user_or_raw_balances(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-wallet-detail",
                kwargs={
                    "pk": self.real_wallet.pk,
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

        self.assertNotIn(
            "user",
            payload,
        )

        self.assertNotIn(
            "user_id",
            payload,
        )

        self.assertNotIn(
            "available_minor",
            payload,
        )

        self.assertNotIn(
            "reserved_minor",
            payload,
        )

    def test_client_cannot_read_another_users_wallet(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse(
                "api:v1-client-wallet-detail",
                kwargs={
                    "pk": self.other_wallet.pk,
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

    def test_wallet_list_is_read_only(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.post(
            reverse(
                "api:v1-client-wallet-list"
            ),
            data={
                "currency": "REAL",
            },
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

    def test_wallet_detail_is_read_only(self):
        token = self._token_for(
            self.client_user
        )

        url = reverse(
            "api:v1-client-wallet-detail",
            kwargs={
                "pk": self.real_wallet.pk,
            },
        )

        for method in (
            "put",
            "patch",
            "delete",
        ):
            with self.subTest(
                method=method,
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

    def test_wallet_get_does_not_create_additional_wallets(self):
        user = User.objects.create_user(
            username="wallet_unchanged",
            email="wallet.unchanged@example.com",
            password="WalletApi123!",
            first_name="Wallet",
            last_name="Unchanged",
            document="API-WALLET-004",
            birth_date=date(2000, 1, 1),
        )

        user.groups.add(
            self.client_group,
        )

        token = self._token_for(
            user
        )

        count_before = Wallet.objects.filter(
            user=user
        ).count()

        response = self.client.get(
            reverse(
                "api:v1-client-wallet-list"
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

        count_after = Wallet.objects.filter(
            user=user
        ).count()

        self.assertEqual(
            count_before,
            2,
        )

        self.assertEqual(
            count_after,
            count_before,
        )

        self.assertEqual(
            len(response.json()),
            count_before,
        )