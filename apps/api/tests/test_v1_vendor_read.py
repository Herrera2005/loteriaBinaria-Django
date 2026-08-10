from __future__ import annotations

import uuid
from datetime import timedelta

from django.test import TestCase
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
from apps.vendors.models import (
    ConversionAssignment,
    ConversionRequest,
    VendorProfile,
)


class ApiV1VendorReadTests(TestCase):
    def setUp(self):
        self.vendor = create_user(
            username="api_vendor_read",
            email="api.vendor.read@example.test",
            document="API-VENDOR-READ",
            roles=(VENDOR,),
        )

        self.profile = VendorProfile.objects.create(
            user=self.vendor,
            status=VendorProfile.Status.ACTIVE,
        )

        self.token = Token.objects.create(
            user=self.vendor,
        )

        self.client_user = create_user(
            username="api_vendor_read_client",
            email="api.vendor.read.client@example.test",
            document="API-VENDOR-READ-CLIENT",
            roles=(CLIENT,),
        )

        self.other_vendor = create_user(
            username="api_vendor_other",
            email="api.vendor.other@example.test",
            document="API-VENDOR-OTHER",
            roles=(VENDOR,),
        )

        self.other_profile = VendorProfile.objects.create(
            user=self.other_vendor,
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

        self.other_wallet = Wallet.objects.get(
            user=self.other_vendor,
            currency=Wallet.Currency.VIRTUAL,
        )

        self.movement = Movement.objects.create(
            wallet=self.virtual_wallet,
            operation_id=uuid.uuid4(),
            type=Movement.Type.WHOLESALE_PURCHASE,
            direction=Movement.Direction.DEBIT,
            amount_minor=1000,
            balance_after_minor=9000,
            description="Movimiento vendedor.",
        )

        self.other_movement = Movement.objects.create(
            wallet=self.other_wallet,
            operation_id=uuid.uuid4(),
            type=Movement.Type.ADJUSTMENT,
            direction=Movement.Direction.CREDIT,
            amount_minor=9999,
            balance_after_minor=9999,
            description="Movimiento ajeno.",
        )

        now = timezone.now()

        self.available_request = (
            ConversionRequest.objects.create(
                client=self.client_user,
                operation_id=uuid.uuid4(),
                amount_minor=2500,
                status=ConversionRequest.Status.PENDING,
                expires_at=(
                    now
                    + timedelta(minutes=5)
                ),
            )
        )

        self.own_request = (
            ConversionRequest.objects.create(
                client=self.vendor,
                operation_id=uuid.uuid4(),
                amount_minor=1000,
                status=ConversionRequest.Status.PENDING,
                expires_at=(
                    now
                    + timedelta(minutes=5)
                ),
            )
        )

        self.assigned_request = (
            ConversionRequest.objects.create(
                client=self.client_user,
                operation_id=uuid.uuid4(),
                amount_minor=1500,
                status=ConversionRequest.Status.IN_PROGRESS,
                expires_at=(
                    now
                    + timedelta(minutes=5)
                ),
            )
        )

        self.assignment = (
            ConversionAssignment.objects.create(
                request=self.assigned_request,
                vendor=self.profile,
                status=ConversionAssignment.Status.ACTIVE,
            )
        )

        self.other_assignment = (
            ConversionAssignment.objects.create(
                request=self.available_request,
                vendor=self.other_profile,
                status=ConversionAssignment.Status.RELEASED,
            )
        )

    def _headers(self):
        return {
            "HTTP_AUTHORIZATION": (
                f"Token {self.token.key}"
            ),
            "HTTP_X_ACTIVE_MODE": VENDOR,
        }

    def test_vendor_wallet_list_returns_own_wallets_only(self):
        response = self.client.get(
            reverse(
                "api:v1-vendor-wallet-list"
            ),
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        ids = {
            row["id"]
            for row in response.json()
        }

        self.assertEqual(
            ids,
            {
                self.real_wallet.pk,
                self.virtual_wallet.pk,
            },
        )

    def test_vendor_cannot_read_other_wallet(self):
        response = self.client.get(
            reverse(
                "api:v1-vendor-wallet-detail",
                kwargs={
                    "pk": self.other_wallet.pk,
                },
            ),
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_vendor_movements_are_isolated(self):
        response = self.client.get(
            reverse(
                "api:v1-vendor-movement-list"
            ),
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        ids = {
            row["id"]
            for row in response.json()["results"]
        }

        self.assertIn(
            self.movement.pk,
            ids,
        )

        self.assertNotIn(
            self.other_movement.pk,
            ids,
        )

    def test_vendor_movement_does_not_expose_operation_id(self):
        response = self.client.get(
            reverse(
                "api:v1-vendor-movement-detail",
                kwargs={
                    "pk": self.movement.pk,
                },
            ),
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotIn(
            "operation_id",
            response.json(),
        )

    def test_available_requests_use_domain_eligibility(self):
        Wallet.objects.filter(
            pk=self.virtual_wallet.pk
        ).update(
            available_minor=10000
        )

        response = self.client.get(
            reverse(
                "api:v1-vendor-request-available-list"
            ),
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        ids = {
            row["id"]
            for row in response.json()["results"]
        }

        self.assertIn(
            self.available_request.pk,
            ids,
        )

        self.assertNotIn(
            self.own_request.pk,
            ids,
        )

        self.assertNotIn(
            self.assigned_request.pk,
            ids,
        )

    def test_available_request_does_not_expose_client_identity(self):
        Wallet.objects.filter(
            pk=self.virtual_wallet.pk
        ).update(
            available_minor=10000
        )

        response = self.client.get(
            reverse(
                "api:v1-vendor-request-available-list"
            ),
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        row = response.json()["results"][0]

        self.assertNotIn(
            "client",
            row,
        )

        self.assertNotIn(
            "operation_id",
            row,
        )

    def test_vendor_assignment_list_returns_only_own_assignments(self):
        response = self.client.get(
            reverse(
                "api:v1-vendor-assignment-list"
            ),
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        ids = {
            row["id"]
            for row in response.json()["results"]
        }

        self.assertEqual(
            ids,
            {
                self.assignment.pk,
            },
        )

    def test_vendor_cannot_read_other_assignment(self):
        response = self.client.get(
            reverse(
                "api:v1-vendor-assignment-detail",
                kwargs={
                    "pk": self.other_assignment.pk,
                },
            ),
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_vendor_read_endpoints_require_vendor_mode(self):
        response = self.client.get(
            reverse(
                "api:v1-vendor-wallet-list"
            ),
            HTTP_AUTHORIZATION=(
                f"Token {self.token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_invalid_vendor_movement_filter_returns_bad_request(self):
        response = self.client.get(
            reverse(
                "api:v1-vendor-movement-list"
            ),
            {
                "currency": "NO_EXISTE",
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
            "currency",
            payload["error"]["fields"],
        )

    def test_invalid_vendor_ordering_returns_bad_request(self):
        response = self.client.get(
            reverse(
                "api:v1-vendor-movement-list"
            ),
            {
                "ordering": "password",
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