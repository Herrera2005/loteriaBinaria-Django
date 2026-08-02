"""Pruebas P-34E: liberar, cancelar y expirar solicitudes."""

from __future__ import annotations

from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.management import call_command
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
    cancel_conversion_request,
    create_conversion_request,
    process_expired_conversion_requests,
    release_conversion_assignment,
)


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


def create_pending_request(*, username: str = "closure_client", amount: int = 2500):
    client = create_client(username=username)
    request, _ = create_conversion_request(
        client=client,
        amount_minor=amount,
        operation_id=f"12345678-1234-5678-1234-{client.pk:012d}",
    )
    return client, request


def create_active_assignment(*, suffix: str = "base", amount: int = 2500):
    client, request = create_pending_request(
        username=f"closure_client_{suffix}",
        amount=amount,
    )
    vendor = create_vendor(username=f"closure_vendor_{suffix}")
    assignment = assign_conversion_request(
        vendor=vendor,
        request_id=request.pk,
    )
    return client, vendor, request, assignment


class ReleaseAssignmentServiceTests(TestCase):
    def test_release_returns_vendor_virtual_and_keeps_client_real_reserved(self):
        client, vendor, request, assignment = create_active_assignment()

        released, released_now = release_conversion_assignment(
            vendor=vendor,
            assignment_id=assignment.pk,
        )

        self.assertTrue(released_now)
        self.assertEqual(released.pk, assignment.pk)
        request.refresh_from_db()
        assignment.refresh_from_db()
        client_real = Wallet.objects.get(
            user=client,
            currency=Wallet.Currency.REAL,
        )
        vendor_virtual = Wallet.objects.get(
            user=vendor,
            currency=Wallet.Currency.VIRTUAL,
        )
        self.assertEqual(client_real.available_minor, 7500)
        self.assertEqual(client_real.reserved_minor, 2500)
        self.assertEqual(vendor_virtual.available_minor, 10000)
        self.assertEqual(vendor_virtual.reserved_minor, 0)
        self.assertEqual(request.status, ConversionRequest.Status.PENDING)
        self.assertEqual(
            assignment.status,
            ConversionAssignment.Status.RELEASED,
        )
        self.assertIsNotNone(assignment.released_at)

    def test_release_is_idempotent_and_other_vendor_is_rejected(self):
        _, vendor, _, assignment = create_active_assignment(suffix="idempotent")
        other_vendor = create_vendor(username="closure_other_vendor")

        with self.assertRaises(ValidationError):
            release_conversion_assignment(
                vendor=other_vendor,
                assignment_id=assignment.pk,
            )

        release_conversion_assignment(
            vendor=vendor,
            assignment_id=assignment.pk,
        )
        movement_count = Movement.objects.count()
        _, released_now = release_conversion_assignment(
            vendor=vendor,
            assignment_id=assignment.pk,
        )
        self.assertFalse(released_now)
        self.assertEqual(Movement.objects.count(), movement_count)


class CancelRequestServiceTests(TestCase):
    def test_client_cancels_pending_request_and_recovers_real(self):
        client, request = create_pending_request(username="cancel_client")

        cancelled, cancelled_now = cancel_conversion_request(
            client=client,
            request_id=request.pk,
        )

        self.assertTrue(cancelled_now)
        self.assertEqual(cancelled.pk, request.pk)
        request.refresh_from_db()
        client_real = Wallet.objects.get(
            user=client,
            currency=Wallet.Currency.REAL,
        )
        self.assertEqual(client_real.available_minor, 10000)
        self.assertEqual(client_real.reserved_minor, 0)
        self.assertEqual(request.status, ConversionRequest.Status.CANCELLED)
        self.assertIsNotNone(request.completed_at)

    def test_client_cannot_cancel_in_progress_request(self):
        client, _, request, _ = create_active_assignment(suffix="no_cancel")

        with self.assertRaises(ValidationError):
            cancel_conversion_request(
                client=client,
                request_id=request.pk,
            )

        request.refresh_from_db()
        self.assertEqual(request.status, ConversionRequest.Status.IN_PROGRESS)


class ExpirationServiceTests(TestCase):
    def test_expired_pending_request_returns_client_real(self):
        client, request = create_pending_request(username="expire_pending")
        future = request.expires_at + timedelta(seconds=1)

        processed = process_expired_conversion_requests(now=future)

        self.assertEqual(processed, 1)
        request.refresh_from_db()
        wallet = Wallet.objects.get(
            user=client,
            currency=Wallet.Currency.REAL,
        )
        self.assertEqual(wallet.available_minor, 10000)
        self.assertEqual(wallet.reserved_minor, 0)
        self.assertEqual(request.status, ConversionRequest.Status.EXPIRED)

    def test_expired_active_assignment_releases_both_reserves(self):
        client, vendor, request, assignment = create_active_assignment(
            suffix="expire_active"
        )
        future = request.expires_at + timedelta(seconds=1)

        processed = process_expired_conversion_requests(now=future)

        self.assertEqual(processed, 1)
        request.refresh_from_db()
        assignment.refresh_from_db()
        client_real = Wallet.objects.get(
            user=client,
            currency=Wallet.Currency.REAL,
        )
        vendor_virtual = Wallet.objects.get(
            user=vendor,
            currency=Wallet.Currency.VIRTUAL,
        )
        self.assertEqual(client_real.available_minor, 10000)
        self.assertEqual(client_real.reserved_minor, 0)
        self.assertEqual(vendor_virtual.available_minor, 10000)
        self.assertEqual(vendor_virtual.reserved_minor, 0)
        self.assertEqual(request.status, ConversionRequest.Status.EXPIRED)
        self.assertEqual(
            assignment.status,
            ConversionAssignment.Status.EXPIRED,
        )

    def test_expiration_is_idempotent(self):
        _, request = create_pending_request(username="expire_twice")
        future = request.expires_at + timedelta(seconds=1)

        first = process_expired_conversion_requests(now=future)
        movements = Movement.objects.count()
        second = process_expired_conversion_requests(now=future)

        self.assertEqual(first, 1)
        self.assertEqual(second, 0)
        self.assertEqual(Movement.objects.count(), movements)

    def test_management_command_reports_processed_count(self):
        _, request = create_pending_request(username="expire_command")
        future = request.expires_at + timedelta(seconds=1)
        output = StringIO()

        with patch(
            "apps.vendors.services.timezone.now",
            return_value=future,
        ):
            call_command("process_expired_requests", stdout=output)

        self.assertIn("Solicitudes vencidas procesadas: 1", output.getvalue())


class RequestClosureViewTests(TestCase):
    def activate(self, user, mode):
        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = mode
        session.save()

    def test_vendor_can_release_from_mine_tab(self):
        _, vendor, request, assignment = create_active_assignment(suffix="view_release")
        self.activate(vendor, VENDOR)

        get_response = self.client.get(
            reverse("core:vendor_requests"),
            {"tab": "mine"},
        )
        self.assertContains(get_response, "Liberar")

        post_response = self.client.post(
            reverse("core:vendor_requests"),
            {
                "action": "release",
                "assignment_id": assignment.pk,
            },
        )
        self.assertRedirects(
            post_response,
            f'{reverse("core:vendor_requests")}?tab=mine',
        )
        request.refresh_from_db()
        self.assertEqual(request.status, ConversionRequest.Status.PENDING)

    def test_client_detail_can_cancel_pending_request(self):
        client, request = create_pending_request(username="cancel_view")
        self.activate(client, CLIENT)
        url = reverse(
            "vendors:client_conversionrequest_detail",
            kwargs={"pk": request.pk},
        )

        get_response = self.client.get(url)
        self.assertContains(get_response, "Cancelar solicitud")

        post_response = self.client.post(url, {})
        self.assertRedirects(post_response, url)
        request.refresh_from_db()
        self.assertEqual(request.status, ConversionRequest.Status.CANCELLED)

    def test_sensitive_posts_require_csrf(self):
        client, vendor, request, assignment = create_active_assignment(
            suffix="csrf"
        )
        csrf_client = Client(enforce_csrf_checks=True)

        csrf_client.force_login(vendor)
        session = csrf_client.session
        session[ACTIVE_MODE_SESSION_KEY] = VENDOR
        session.save()
        vendor_response = csrf_client.post(
            reverse("core:vendor_requests"),
            {"action": "release", "assignment_id": assignment.pk},
        )
        self.assertEqual(vendor_response.status_code, 403)

        csrf_client.force_login(client)
        session = csrf_client.session
        session[ACTIVE_MODE_SESSION_KEY] = CLIENT
        session.save()
        client_response = csrf_client.post(
            reverse(
                "vendors:client_conversionrequest_detail",
                kwargs={"pk": request.pk},
            ),
            {},
        )
        self.assertEqual(client_response.status_code, 403)
