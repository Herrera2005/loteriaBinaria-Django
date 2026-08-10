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
    VendorInventoryPurchase,
    Wallet,
)
from apps.finance.services import (
    purchase_vendor_inventory,
)
from apps.vendors.models import VendorProfile


class ApiV1VendorInventoryTests(TestCase):
    def setUp(self):
        self.vendor = create_user(
            username="api_vendor_inventory",
            email="api.vendor.inventory@example.test",
            document="API-VENDOR-INVENTORY",
            roles=(VENDOR,),
        )

        self.profile = VendorProfile.objects.create(
            user=self.vendor,
            status=VendorProfile.Status.ACTIVE,
        )

        self.real_wallet = Wallet.objects.get(
            user=self.vendor,
            currency=Wallet.Currency.REAL,
        )

        self.virtual_wallet = Wallet.objects.get(
            user=self.vendor,
            currency=Wallet.Currency.VIRTUAL,
        )

        Wallet.objects.filter(
            pk=self.real_wallet.pk,
        ).update(
            available_minor=20000,
            reserved_minor=0,
        )

        Wallet.objects.filter(
            pk=self.virtual_wallet.pk,
        ).update(
            available_minor=0,
            reserved_minor=0,
        )

        self.token = Token.objects.create(
            user=self.vendor,
        )

        self.url = reverse(
            "api:v1-vendor-inventory-purchase-list"
        )

    def _headers(
        self,
        *,
        operation_id=None,
        mode=VENDOR,
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
        virtual_minor=10000,
        operation_id=None,
        mode=VENDOR,
    ):
        return self.client.post(
            self.url,
            data={
                "virtual_minor": virtual_minor,
            },
            content_type="application/json",
            **self._headers(
                operation_id=operation_id,
                mode=mode,
            ),
        )

    def test_inventory_purchase_requires_authentication(self):
        response = self.client.post(
            self.url,
            data={
                "virtual_minor": 10000,
            },
            content_type="application/json",
            HTTP_X_ACTIVE_MODE=VENDOR,
            HTTP_IDEMPOTENCY_KEY=str(
                uuid.uuid4()
            ),
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_inventory_purchase_requires_vendor_mode(self):
        response = self._purchase(
            operation_id=uuid.uuid4(),
            mode=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_inventory_purchase_requires_idempotency_key(self):
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

    def test_inventory_purchase_rejects_invalid_idempotency_key(self):
        response = self.client.post(
            self.url,
            data={
                "virtual_minor": 10000,
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=(
                f"Token {self.token.key}"
            ),
            HTTP_X_ACTIVE_MODE=VENDOR,
            HTTP_IDEMPOTENCY_KEY=(
                "uuid-invalido"
            ),
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            VendorInventoryPurchase.objects.exists()
        )

    def test_purchase_100_virtual_costs_90_real(self):
        operation_id = uuid.uuid4()

        response = self._purchase(
            virtual_minor=10000,
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

        purchase = (
            VendorInventoryPurchase.objects.get(
                operation_id=operation_id
            )
        )

        self.assertEqual(
            purchase.amount_minor,
            10000,
        )

        self.assertEqual(
            purchase.cost_real_minor,
            9000,
        )

        self.assertEqual(
            payload["purchase"]["virtual"],
            {
                "minor": 10000,
                "currency": "VIRTUAL",
                "display": "V 100.00",
            },
        )

        self.assertEqual(
            payload["purchase"]["real_cost"],
            {
                "minor": 9000,
                "currency": "REAL",
                "display": "$ 90.00",
            },
        )

        self.real_wallet.refresh_from_db()
        self.virtual_wallet.refresh_from_db()

        self.assertEqual(
            self.real_wallet.available_minor,
            11000,
        )

        self.assertEqual(
            self.virtual_wallet.available_minor,
            10000,
        )

    def test_inventory_purchase_creates_two_correlated_movements(self):
        operation_id = uuid.uuid4()

        response = self._purchase(
            virtual_minor=10000,
            operation_id=operation_id,
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        movements = Movement.objects.filter(
            operation_id=operation_id,
            type=Movement.Type.WHOLESALE_PURCHASE,
        )

        self.assertEqual(
            movements.count(),
            2,
        )

        self.assertTrue(
            movements.filter(
                wallet=self.real_wallet,
                direction=Movement.Direction.DEBIT,
                amount_minor=9000,
            ).exists()
        )

        self.assertTrue(
            movements.filter(
                wallet=self.virtual_wallet,
                direction=Movement.Direction.CREDIT,
                amount_minor=10000,
            ).exists()
        )

    def test_same_idempotency_key_does_not_charge_twice(self):
        operation_id = uuid.uuid4()

        first = self._purchase(
            virtual_minor=10000,
            operation_id=operation_id,
        )

        second = self._purchase(
            virtual_minor=10000,
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
            first.json()["purchase"]["id"],
            second.json()["purchase"]["id"],
        )

        self.assertEqual(
            VendorInventoryPurchase.objects.filter(
                operation_id=operation_id
            ).count(),
            1,
        )

        self.assertEqual(
            Movement.objects.filter(
                operation_id=operation_id
            ).count(),
            2,
        )

        self.real_wallet.refresh_from_db()
        self.virtual_wallet.refresh_from_db()

        self.assertEqual(
            self.real_wallet.available_minor,
            11000,
        )

        self.assertEqual(
            self.virtual_wallet.available_minor,
            10000,
        )

    def test_same_idempotency_key_with_different_amount_is_rejected(self):
        operation_id = uuid.uuid4()

        first = self._purchase(
            virtual_minor=10000,
            operation_id=operation_id,
        )

        self.assertEqual(
            first.status_code,
            201,
        )

        second = self._purchase(
            virtual_minor=5000,
            operation_id=operation_id,
        )

        self.assertEqual(
            second.status_code,
            400,
        )

        self.assertEqual(
            VendorInventoryPurchase.objects.filter(
                operation_id=operation_id
            ).count(),
            1,
        )

        self.assertEqual(
            Movement.objects.filter(
                operation_id=operation_id
            ).count(),
            2,
        )

    def test_inventory_purchase_requires_complete_virtual_units(self):
        operation_id = uuid.uuid4()

        response = self._purchase(
            virtual_minor=1050,
            operation_id=operation_id,
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            VendorInventoryPurchase.objects.filter(
                operation_id=operation_id
            ).exists()
        )

        self.real_wallet.refresh_from_db()
        self.virtual_wallet.refresh_from_db()

        self.assertEqual(
            self.real_wallet.available_minor,
            20000,
        )

        self.assertEqual(
            self.virtual_wallet.available_minor,
            0,
        )

    def test_insufficient_real_balance_has_no_effects(self):
        Wallet.objects.filter(
            pk=self.real_wallet.pk,
        ).update(
            available_minor=5000,
        )

        operation_id = uuid.uuid4()

        response = self._purchase(
            virtual_minor=10000,
            operation_id=operation_id,
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            VendorInventoryPurchase.objects.filter(
                operation_id=operation_id
            ).exists()
        )

        self.assertFalse(
            Movement.objects.filter(
                operation_id=operation_id
            ).exists()
        )

        self.real_wallet.refresh_from_db()
        self.virtual_wallet.refresh_from_db()

        self.assertEqual(
            self.real_wallet.available_minor,
            5000,
        )

        self.assertEqual(
            self.virtual_wallet.available_minor,
            0,
        )

    def test_vendor_inventory_history_only_contains_own_purchases(self):
        own_purchase, _ = purchase_vendor_inventory(
            vendor=self.vendor,
            virtual_minor=10000,
            operation_id=uuid.uuid4(),
        )

        other_vendor = create_user(
            username="api_other_inventory_vendor",
            email="api.other.inventory@example.test",
            document="API-OTHER-INVENTORY",
            roles=(VENDOR,),
        )

        VendorProfile.objects.create(
            user=other_vendor,
            status=VendorProfile.Status.ACTIVE,
        )

        other_real = Wallet.objects.get(
            user=other_vendor,
            currency=Wallet.Currency.REAL,
        )

        Wallet.objects.filter(
            pk=other_real.pk,
        ).update(
            available_minor=20000,
        )

        other_purchase, _ = (
            purchase_vendor_inventory(
                vendor=other_vendor,
                virtual_minor=10000,
                operation_id=uuid.uuid4(),
            )
        )

        response = self.client.get(
            self.url,
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        ids = {
            row["id"]
            for row
            in response.json()["results"]
        }

        self.assertIn(
            own_purchase.pk,
            ids,
        )

        self.assertNotIn(
            other_purchase.pk,
            ids,
        )

    def test_inventory_contract_does_not_expose_internal_fields(self):
        purchase, _ = purchase_vendor_inventory(
            vendor=self.vendor,
            virtual_minor=10000,
            operation_id=uuid.uuid4(),
        )

        response = self.client.get(
            reverse(
                "api:v1-vendor-inventory-purchase-detail",
                kwargs={
                    "pk": purchase.pk,
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
            "user",
            payload,
        )

        self.assertNotIn(
            "user_id",
            payload,
        )

        self.assertNotIn(
            "amount_minor",
            payload,
        )

        self.assertNotIn(
            "cost_real_minor",
            payload,
        )