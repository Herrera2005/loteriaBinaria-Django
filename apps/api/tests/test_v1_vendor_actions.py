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
from apps.vendors.models import (
    ConversionAssignment,
    ConversionRequest,
    VendorProfile,
)
from apps.vendors.services import (
    assign_conversion_request,
    create_conversion_request,
)


class ApiV1VendorActionTests(TestCase):
    def setUp(self):
        self.client_user = create_user(
            username="api_vendor_action_client",
            email="api.vendor.action.client@example.test",
            document="API-VENDOR-ACTION-CLIENT",
            roles=(CLIENT,),
        )

        self.vendor = create_user(
            username="api_vendor_action_vendor",
            email="api.vendor.action.vendor@example.test",
            document="API-VENDOR-ACTION-VENDOR",
            roles=(VENDOR,),
        )

        self.vendor_profile = VendorProfile.objects.create(
            user=self.vendor,
            status=VendorProfile.Status.ACTIVE,
        )

        self.other_vendor = create_user(
            username="api_vendor_action_other",
            email="api.vendor.action.other@example.test",
            document="API-VENDOR-ACTION-OTHER",
            roles=(VENDOR,),
        )

        self.other_vendor_profile = VendorProfile.objects.create(
            user=self.other_vendor,
            status=VendorProfile.Status.ACTIVE,
        )

        self.client_real = Wallet.objects.get(
            user=self.client_user,
            currency=Wallet.Currency.REAL,
        )

        self.client_virtual = Wallet.objects.get(
            user=self.client_user,
            currency=Wallet.Currency.VIRTUAL,
        )

        self.vendor_real = Wallet.objects.get(
            user=self.vendor,
            currency=Wallet.Currency.REAL,
        )

        self.vendor_virtual = Wallet.objects.get(
            user=self.vendor,
            currency=Wallet.Currency.VIRTUAL,
        )

        self.other_vendor_virtual = Wallet.objects.get(
            user=self.other_vendor,
            currency=Wallet.Currency.VIRTUAL,
        )

        Wallet.objects.filter(
            pk=self.client_real.pk,
        ).update(
            available_minor=10000,
            reserved_minor=0,
        )

        Wallet.objects.filter(
            pk=self.client_virtual.pk,
        ).update(
            available_minor=0,
            reserved_minor=0,
        )

        Wallet.objects.filter(
            pk=self.vendor_real.pk,
        ).update(
            available_minor=0,
            reserved_minor=0,
        )

        Wallet.objects.filter(
            pk=self.vendor_virtual.pk,
        ).update(
            available_minor=10000,
            reserved_minor=0,
        )

        Wallet.objects.filter(
            pk=self.other_vendor_virtual.pk,
        ).update(
            available_minor=10000,
            reserved_minor=0,
        )

        self.token = Token.objects.create(
            user=self.vendor,
        )

        self.other_vendor_token = Token.objects.create(
            user=self.other_vendor,
        )

    def _headers(
        self,
        *,
        token=None,
        mode=VENDOR,
    ):
        token = token or self.token

        return {
            "HTTP_AUTHORIZATION": (
                f"Token {token.key}"
            ),
            "HTTP_X_ACTIVE_MODE": mode,
        }

    def _create_request(
        self,
        *,
        amount_minor=2500,
        client=None,
    ):
        client = client or self.client_user

        request_obj, created = create_conversion_request(
            client=client,
            amount_minor=amount_minor,
            operation_id=uuid.uuid4(),
        )

        self.assertTrue(created)

        return request_obj

    def _assign_url(
        self,
        request_obj,
    ):
        return reverse(
            "api:v1-vendor-request-assign",
            kwargs={
                "pk": request_obj.pk,
            },
        )

    def _complete_url(
        self,
        assignment,
    ):
        return reverse(
            "api:v1-vendor-assignment-complete",
            kwargs={
                "pk": assignment.pk,
            },
        )

    def _release_url(
        self,
        assignment,
    ):
        return reverse(
            "api:v1-vendor-assignment-release",
            kwargs={
                "pk": assignment.pk,
            },
        )

    def test_assign_requires_authentication(self):
        request_obj = self._create_request()

        response = self.client.post(
            self._assign_url(
                request_obj
            ),
            data={},
            content_type="application/json",
            HTTP_X_ACTIVE_MODE=VENDOR,
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_assign_requires_vendor_mode(self):
        request_obj = self._create_request()

        response = self.client.post(
            self._assign_url(
                request_obj
            ),
            data={},
            content_type="application/json",
            **self._headers(
                mode=CLIENT,
            ),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_vendor_can_assign_eligible_request(self):
        request_obj = self._create_request(
            amount_minor=2500,
        )

        response = self.client.post(
            self._assign_url(
                request_obj
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        payload = response.json()

        self.assertTrue(
            payload["created"]
        )

        assignment = ConversionAssignment.objects.get(
            pk=payload["assignment"]["id"]
        )

        request_obj.refresh_from_db()

        self.assertEqual(
            request_obj.status,
            ConversionRequest.Status.IN_PROGRESS,
        )

        self.assertEqual(
            assignment.status,
            ConversionAssignment.Status.ACTIVE,
        )

        self.assertEqual(
            assignment.vendor_id,
            self.vendor_profile.pk,
        )

        self.vendor_virtual.refresh_from_db()

        self.assertEqual(
            self.vendor_virtual.available_minor,
            7500,
        )

        self.assertEqual(
            self.vendor_virtual.reserved_minor,
            2500,
        )

    def test_same_request_cannot_be_assigned_twice(self):
        request_obj = self._create_request()

        first = self.client.post(
            self._assign_url(
                request_obj
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            first.status_code,
            201,
        )

        second = self.client.post(
            self._assign_url(
                request_obj
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            second.status_code,
            400,
        )

        self.assertEqual(
            ConversionAssignment.objects.filter(
                request=request_obj,
                status=ConversionAssignment.Status.ACTIVE,
            ).count(),
            1,
        )

        self.vendor_virtual.refresh_from_db()

        self.assertEqual(
            self.vendor_virtual.available_minor,
            7500,
        )

        self.assertEqual(
            self.vendor_virtual.reserved_minor,
            2500,
        )

    def test_other_vendor_cannot_take_already_assigned_request(self):
        request_obj = self._create_request()

        first = self.client.post(
            self._assign_url(
                request_obj
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            first.status_code,
            201,
        )

        second = self.client.post(
            self._assign_url(
                request_obj
            ),
            data={},
            content_type="application/json",
            **self._headers(
                token=self.other_vendor_token,
            ),
        )

        self.assertEqual(
            second.status_code,
            400,
        )

        self.other_vendor_virtual.refresh_from_db()

        self.assertEqual(
            self.other_vendor_virtual.available_minor,
            10000,
        )

        self.assertEqual(
            self.other_vendor_virtual.reserved_minor,
            0,
        )

    def test_vendor_cannot_assign_own_request(self):
        multirole_vendor = create_user(
            username="api_vendor_own_request",
            email="api.vendor.own.request@example.test",
            document="API-VENDOR-OWN-REQUEST",
            roles=(
                CLIENT,
                VENDOR,
            ),
        )

        multirole_profile = VendorProfile.objects.create(
            user=multirole_vendor,
           status=VendorProfile.Status.ACTIVE,
        )

        multirole_real = Wallet.objects.get(
            user=multirole_vendor,
            currency=Wallet.Currency.REAL,
        )

        multirole_virtual = Wallet.objects.get(
            user=multirole_vendor,
            currency=Wallet.Currency.VIRTUAL,
        )

        Wallet.objects.filter(
            pk=multirole_real.pk,
        ).update(
            available_minor=5000,
            reserved_minor=0,
        )

        Wallet.objects.filter(
            pk=multirole_virtual.pk,
        ).update(
            available_minor=5000,
            reserved_minor=0,
        )

        token = Token.objects.create(
            user=multirole_vendor,
        )

        own_request, created = create_conversion_request(
            client=multirole_vendor,
            amount_minor=1000,
            operation_id=uuid.uuid4(),
        )

        self.assertTrue(created)

        multirole_real.refresh_from_db()

        self.assertEqual(
            multirole_real.available_minor,
            4000,
        )

        self.assertEqual(
            multirole_real.reserved_minor,
            1000,
        )

        response = self.client.post(
            self._assign_url(
                own_request
            ),
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=VENDOR,
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

        own_request.refresh_from_db()

        self.assertEqual(
            own_request.status,
            ConversionRequest.Status.PENDING,
        )

        self.assertFalse(
            ConversionAssignment.objects.filter(
                request=own_request,
            ).exists()
        )

        multirole_virtual.refresh_from_db()

        self.assertEqual(
            multirole_virtual.available_minor,
            5000,
        )

        self.assertEqual(
            multirole_virtual.reserved_minor,
            0,
        )

    def test_insufficient_vendor_inventory_rejects_assignment_without_effects(self):
        Wallet.objects.filter(
            pk=self.vendor_virtual.pk,
        ).update(
            available_minor=500,
            reserved_minor=0,
        )

        request_obj = self._create_request(
            amount_minor=2500,
        )

        response = self.client.post(
            self._assign_url(
                request_obj
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        request_obj.refresh_from_db()

        self.assertEqual(
            request_obj.status,
            ConversionRequest.Status.PENDING,
        )

        self.assertFalse(
            ConversionAssignment.objects.filter(
                request=request_obj
            ).exists()
        )

        self.vendor_virtual.refresh_from_db()

        self.assertEqual(
            self.vendor_virtual.available_minor,
            500,
        )

        self.assertEqual(
            self.vendor_virtual.reserved_minor,
            0,
        )

    def test_assign_missing_request_returns_bad_request_from_domain(self):
        response = self.client.post(
            reverse(
                "api:v1-vendor-request-assign",
                kwargs={
                    "pk": 999999,
                },
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.json()["error"]["code"],
            "BAD_REQUEST",
        )

    def test_complete_assignment_moves_all_balances(self):
        request_obj = self._create_request(
            amount_minor=2500,
        )

        assignment = assign_conversion_request(
            vendor=self.vendor,
            request_id=request_obj.pk,
        )

        self.client_real.refresh_from_db()
        self.client_virtual.refresh_from_db()
        self.vendor_real.refresh_from_db()
        self.vendor_virtual.refresh_from_db()

        self.assertEqual(
            self.client_real.available_minor,
            7500,
        )

        self.assertEqual(
            self.client_real.reserved_minor,
            2500,
        )

        self.assertEqual(
            self.vendor_virtual.available_minor,
            7500,
        )

        self.assertEqual(
            self.vendor_virtual.reserved_minor,
            2500,
        )

        response = self.client.post(
            self._complete_url(
                assignment
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertTrue(
            payload["completed_now"]
        )

        request_obj.refresh_from_db()
        assignment.refresh_from_db()

        self.client_real.refresh_from_db()
        self.client_virtual.refresh_from_db()
        self.vendor_real.refresh_from_db()
        self.vendor_virtual.refresh_from_db()

        self.assertEqual(
            request_obj.status,
            ConversionRequest.Status.COMPLETED_BY_VENDOR,
        )

        self.assertEqual(
            assignment.status,
            ConversionAssignment.Status.COMPLETED,
        )

        self.assertIsNotNone(
            request_obj.completed_at
        )

        self.assertIsNotNone(
            assignment.completed_at
        )

        self.assertEqual(
            self.client_real.available_minor,
            7500,
        )

        self.assertEqual(
            self.client_real.reserved_minor,
            0,
        )

        self.assertEqual(
            self.client_virtual.available_minor,
            2500,
        )

        self.assertEqual(
            self.vendor_virtual.available_minor,
            7500,
        )

        self.assertEqual(
            self.vendor_virtual.reserved_minor,
            0,
        )

        self.assertEqual(
            self.vendor_real.available_minor,
            2500,
        )

    def test_complete_creates_expected_correlated_movements(self):
        request_obj = self._create_request(
            amount_minor=2500,
        )

        assignment = assign_conversion_request(
            vendor=self.vendor,
            request_id=request_obj.pk,
        )

        response = self.client.post(
            self._complete_url(
                assignment
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        movements = Movement.objects.filter(
            operation_id=request_obj.operation_id
        )

        self.assertEqual(
            movements.count(),
            4,
        )

        self.assertTrue(
            movements.filter(
                wallet=self.client_real,
                direction=Movement.Direction.DEBIT,
                amount_minor=2500,
            ).exists()
        )

        self.assertTrue(
            movements.filter(
                wallet=self.client_virtual,
                direction=Movement.Direction.CREDIT,
                amount_minor=2500,
            ).exists()
        )

        self.assertTrue(
            movements.filter(
                wallet=self.vendor_virtual,
                direction=Movement.Direction.DEBIT,
                amount_minor=2500,
            ).exists()
        )

        self.assertTrue(
            movements.filter(
                wallet=self.vendor_real,
                direction=Movement.Direction.CREDIT,
                amount_minor=2500,
            ).exists()
        )

    def test_complete_is_idempotent(self):
        request_obj = self._create_request()

        assignment = assign_conversion_request(
            vendor=self.vendor,
            request_id=request_obj.pk,
        )

        first = self.client.post(
            self._complete_url(
                assignment
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        second = self.client.post(
            self._complete_url(
                assignment
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            first.status_code,
            200,
        )

        self.assertEqual(
            second.status_code,
            200,
        )

        self.assertTrue(
            first.json()["completed_now"]
        )

        self.assertFalse(
            second.json()["completed_now"]
        )

        self.client_virtual.refresh_from_db()
        self.vendor_real.refresh_from_db()

        self.assertEqual(
            self.client_virtual.available_minor,
            2500,
        )

        self.assertEqual(
            self.vendor_real.available_minor,
            2500,
        )

        self.assertEqual(
            Movement.objects.filter(
                operation_id=request_obj.operation_id
            ).count(),
            4,
        )

    def test_other_vendor_cannot_complete_assignment(self):
        request_obj = self._create_request()

        assignment = assign_conversion_request(
            vendor=self.vendor,
            request_id=request_obj.pk,
        )

        response = self.client.post(
            self._complete_url(
                assignment
            ),
            data={},
            content_type="application/json",
            **self._headers(
                token=self.other_vendor_token,
            ),
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        assignment.refresh_from_db()
        request_obj.refresh_from_db()

        self.assertEqual(
            assignment.status,
            ConversionAssignment.Status.ACTIVE,
        )

        self.assertEqual(
            request_obj.status,
            ConversionRequest.Status.IN_PROGRESS,
        )

    def test_release_returns_reserved_virtual_and_request_to_pending(self):
        request_obj = self._create_request(
            amount_minor=2500,
        )

        assignment = assign_conversion_request(
            vendor=self.vendor,
            request_id=request_obj.pk,
        )

        self.vendor_virtual.refresh_from_db()

        self.assertEqual(
            self.vendor_virtual.available_minor,
            7500,
        )

        self.assertEqual(
            self.vendor_virtual.reserved_minor,
            2500,
        )

        response = self.client.post(
            self._release_url(
                assignment
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.json()["released_now"]
        )

        assignment.refresh_from_db()
        request_obj.refresh_from_db()
        self.vendor_virtual.refresh_from_db()

        self.assertEqual(
            assignment.status,
            ConversionAssignment.Status.RELEASED,
        )

        self.assertIsNotNone(
            assignment.released_at
        )

        self.assertEqual(
            request_obj.status,
            ConversionRequest.Status.PENDING,
        )

        self.assertEqual(
            self.vendor_virtual.available_minor,
            10000,
        )

        self.assertEqual(
            self.vendor_virtual.reserved_minor,
            0,
        )

    def test_release_is_idempotent(self):
        request_obj = self._create_request()

        assignment = assign_conversion_request(
            vendor=self.vendor,
            request_id=request_obj.pk,
        )

        first = self.client.post(
            self._release_url(
                assignment
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        second = self.client.post(
            self._release_url(
                assignment
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            first.status_code,
            200,
        )

        self.assertEqual(
            second.status_code,
            200,
        )

        self.assertTrue(
            first.json()["released_now"]
        )

        self.assertFalse(
            second.json()["released_now"]
        )

        self.vendor_virtual.refresh_from_db()

        self.assertEqual(
            self.vendor_virtual.available_minor,
            10000,
        )

        self.assertEqual(
            self.vendor_virtual.reserved_minor,
            0,
        )

        release_movements = (
            Movement.objects.filter(
                operation_id=request_obj.operation_id,
                wallet=self.vendor_virtual,
                direction=Movement.Direction.CREDIT,
            )
        )

        self.assertEqual(
            release_movements.count(),
            1,
        )

    def test_other_vendor_cannot_release_assignment(self):
        request_obj = self._create_request()

        assignment = assign_conversion_request(
            vendor=self.vendor,
            request_id=request_obj.pk,
        )

        response = self.client.post(
            self._release_url(
                assignment
            ),
            data={},
            content_type="application/json",
            **self._headers(
                token=self.other_vendor_token,
            ),
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        assignment.refresh_from_db()
        request_obj.refresh_from_db()

        self.assertEqual(
            assignment.status,
            ConversionAssignment.Status.ACTIVE,
        )

        self.assertEqual(
            request_obj.status,
            ConversionRequest.Status.IN_PROGRESS,
        )

    def test_released_request_becomes_available_again(self):
        request_obj = self._create_request(
            amount_minor=2500,
        )

        assignment = assign_conversion_request(
            vendor=self.vendor,
            request_id=request_obj.pk,
        )

        release_response = self.client.post(
            self._release_url(
                assignment
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            release_response.status_code,
            200,
        )

        available_response = self.client.get(
            reverse(
                "api:v1-vendor-request-available-list"
            ),
            **self._headers(),
        )

        self.assertEqual(
            available_response.status_code,
            200,
        )

        ids = {
            row["id"]
            for row
            in available_response.json()["results"]
        }

        self.assertIn(
            request_obj.pk,
            ids,
        )

    def test_suspended_vendor_profile_cannot_execute_actions(self):
        request_obj = self._create_request()

        self.vendor_profile.status = (
            VendorProfile.Status.SUSPENDED
        )

        self.vendor_profile.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        response = self.client.post(
            self._assign_url(
                request_obj
            ),
            data={},
            content_type="application/json",
            **self._headers(),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        request_obj.refresh_from_db()

        self.assertEqual(
            request_obj.status,
            ConversionRequest.Status.PENDING,
        )

        self.assertFalse(
            ConversionAssignment.objects.filter(
                request=request_obj
            ).exists()
        )