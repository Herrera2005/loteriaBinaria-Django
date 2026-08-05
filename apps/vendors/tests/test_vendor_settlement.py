"""Pruebas P-34D: liquidación de solicitudes por el Vendedor."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import CLIENT, VENDOR
from apps.accounts.tests.factories import create_user
from apps.finance.models import Movement, Wallet
from apps.vendors.models import (
    ConversionAssignment,
    ConversionRequest,
    VendorProfile,
)
from apps.vendors.services import (
    assign_conversion_request,
    complete_conversion_request,
    create_conversion_request,
)


def create_vendor(*, username: str, virtual_minor: int = 10000):
    user = create_user(
        username=username,
        email=f"{username}@example.test",
        document=f"V-{username}",
        roles=(VENDOR,),
    )
    VendorProfile.objects.create(
        user=user,
        status=VendorProfile.Status.ACTIVE,
    )
    Wallet.objects.filter(
        user=user,
        currency=Wallet.Currency.VIRTUAL,
    ).update(available_minor=virtual_minor)
    return user


def create_client(*, username: str, real_minor: int = 10000):
    user = create_user(
        username=username,
        email=f"{username}@example.test",
        document=f"C-{username}",
        roles=(CLIENT,),
    )
    Wallet.objects.filter(
        user=user,
        currency=Wallet.Currency.REAL,
    ).update(available_minor=real_minor)
    return user


def prepare_assignment(*, amount_minor: int = 2500):
    client = create_client(username="settlement_client")
    vendor = create_vendor(username="settlement_vendor")
    request, _ = create_conversion_request(
        client=client,
        amount_minor=amount_minor,
        operation_id="12345678-1234-5678-1234-567812345678",
    )
    assignment = assign_conversion_request(
        vendor=vendor,
        request_id=request.pk,
    )
    return client, vendor, request, assignment


class CompleteConversionRequestServiceTests(TestCase):
    def test_completion_transfers_both_currencies_and_closes_flow(self):
        client, vendor, request, assignment = prepare_assignment()

        completed, completed_now = complete_conversion_request(
            vendor=vendor,
            assignment_id=assignment.pk,
        )

        self.assertTrue(completed_now)
        self.assertEqual(completed.pk, assignment.pk)

        request.refresh_from_db()
        assignment.refresh_from_db()
        client_real = Wallet.objects.get(
            user=client,
            currency=Wallet.Currency.REAL,
        )
        client_virtual = Wallet.objects.get(
            user=client,
            currency=Wallet.Currency.VIRTUAL,
        )
        vendor_real = Wallet.objects.get(
            user=vendor,
            currency=Wallet.Currency.REAL,
        )
        vendor_virtual = Wallet.objects.get(
            user=vendor,
            currency=Wallet.Currency.VIRTUAL,
        )

        self.assertEqual(client_real.available_minor, 7500)
        self.assertEqual(client_real.reserved_minor, 0)
        self.assertEqual(client_virtual.available_minor, 2500)
        self.assertEqual(vendor_real.available_minor, 2500)
        self.assertEqual(vendor_virtual.available_minor, 7500)
        self.assertEqual(vendor_virtual.reserved_minor, 0)
        self.assertEqual(
            request.status,
            ConversionRequest.Status.COMPLETED_BY_VENDOR,
        )
        self.assertIsNotNone(request.completed_at)
        self.assertEqual(
            assignment.status,
            ConversionAssignment.Status.COMPLETED,
        )
        self.assertIsNotNone(assignment.completed_at)

        movements = Movement.objects.filter(operation_id=request.operation_id)
        self.assertEqual(movements.count(), 4)
        self.assertTrue(
            movements.filter(
                wallet=client_virtual,
                direction=Movement.Direction.CREDIT,
                amount_minor=2500,
            ).exists()
        )
        self.assertTrue(
            movements.filter(
                wallet=vendor_real,
                direction=Movement.Direction.CREDIT,
                amount_minor=2500,
            ).exists()
        )

    def test_repeated_completion_is_idempotent(self):
        client, vendor, request, assignment = prepare_assignment()
        complete_conversion_request(
            vendor=vendor,
            assignment_id=assignment.pk,
        )
        movement_count = Movement.objects.count()

        _, completed_now = complete_conversion_request(
            vendor=vendor,
            assignment_id=assignment.pk,
        )

        self.assertFalse(completed_now)
        self.assertEqual(Movement.objects.count(), movement_count)
        self.assertEqual(
            Wallet.objects.get(
                user=client,
                currency=Wallet.Currency.VIRTUAL,
            ).available_minor,
            2500,
        )

    def test_other_vendor_cannot_complete_assignment(self):
        _, vendor, _, assignment = prepare_assignment()
        other_vendor = create_vendor(username="other_settlement_vendor")

        with self.assertRaises(ValidationError):
            complete_conversion_request(
                vendor=other_vendor,
                assignment_id=assignment.pk,
            )

        assignment.refresh_from_db()
        self.assertEqual(assignment.status, ConversionAssignment.Status.ACTIVE)

    def test_expired_assignment_cannot_be_completed(self):
        _, vendor, request, assignment = prepare_assignment()
        future = request.expires_at + timedelta(seconds=1)

        with patch(
            "apps.vendors.services.timezone.now",
            return_value=future,
        ):
            with self.assertRaises(ValidationError):
                complete_conversion_request(
                    vendor=vendor,
                    assignment_id=assignment.pk,
                )

        request.refresh_from_db()
        assignment.refresh_from_db()
        self.assertEqual(request.status, ConversionRequest.Status.IN_PROGRESS)
        self.assertEqual(assignment.status, ConversionAssignment.Status.ACTIVE)

    def test_insufficient_reserved_balance_rolls_back(self):
        client, vendor, request, assignment = prepare_assignment()
        Wallet.objects.filter(
            user=vendor,
            currency=Wallet.Currency.VIRTUAL,
        ).update(reserved_minor=0)
        before_movements = Movement.objects.count()

        with self.assertRaises(ValidationError):
            complete_conversion_request(
                vendor=vendor,
                assignment_id=assignment.pk,
            )

        request.refresh_from_db()
        assignment.refresh_from_db()
        self.assertEqual(request.status, ConversionRequest.Status.IN_PROGRESS)
        self.assertEqual(assignment.status, ConversionAssignment.Status.ACTIVE)
        self.assertEqual(Movement.objects.count(), before_movements)
        self.assertEqual(
            Wallet.objects.get(
                user=client,
                currency=Wallet.Currency.VIRTUAL,
            ).available_minor,
            0,
        )


class CompleteConversionRequestViewTests(TestCase):
    def setUp(self):
        self.client_user, self.vendor, self.request, self.assignment = (
            prepare_assignment()
        )
        self.client.force_login(self.vendor)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = VENDOR
        session.save()

    def test_mine_tab_shows_complete_action(self):
        response = self.client.get(
            reverse("core:vendor_requests"),
            {"tab": "mine"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Completar solicitud")
        self.assertContains(response, f'value="{self.assignment.pk}"')

    def test_post_completes_and_redirects_to_mine_tab(self):
        response = self.client.post(
            reverse("core:vendor_requests"),
            {
                "action": "complete",
                "assignment_id": self.assignment.pk,
            },
        )

        self.assertRedirects(
            response,
            f'{reverse("core:vendor_requests")}?tab=mine',
        )
        self.request.refresh_from_db()
        self.assertEqual(
            self.request.status,
            ConversionRequest.Status.COMPLETED_BY_VENDOR,
        )

    def test_completion_post_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.vendor)
        session = csrf_client.session
        session[ACTIVE_MODE_SESSION_KEY] = VENDOR
        session.save()

        response = csrf_client.post(
            reverse("core:vendor_requests"),
            {
                "action": "complete",
                "assignment_id": self.assignment.pk,
            },
        )

        self.assertEqual(response.status_code, 403)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, ConversionRequest.Status.IN_PROGRESS)
