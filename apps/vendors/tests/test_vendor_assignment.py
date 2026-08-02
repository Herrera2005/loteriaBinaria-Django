"""Pruebas P-34C: cola elegible y toma transaccional de solicitudes."""

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
from apps.finance.models import Wallet
from apps.vendors.models import (
    ConversionAssignment,
    ConversionRequest,
    VendorProfile,
)
from apps.vendors.services import (
    assign_conversion_request,
    eligible_conversion_requests,
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


def create_client(*, username: str):
    return create_user(
        username=username,
        email=f"{username}@example.test",
        document=f"C-{username}",
        roles=(CLIENT,),
    )


def create_request(*, client, amount_minor=2500, minutes=5):
    return ConversionRequest.objects.create(
        client=client,
        amount_minor=amount_minor,
        status=ConversionRequest.Status.PENDING,
        expires_at=timezone.now() + timedelta(minutes=minutes),
    )


class EligibleConversionRequestTests(TestCase):
    def test_only_eligible_requests_are_returned(self):
        vendor = create_vendor(
            username="eligible_vendor",
            virtual_minor=5000,
        )
        other_client = create_client(username="eligible_client")

        visible = create_request(
            client=other_client,
            amount_minor=4000,
            minutes=5,
        )

        # No aparece porque supera el inventario VIRTUAL del vendedor.
        create_request(
            client=other_client,
            amount_minor=6000,
            minutes=5,
        )

        # Se crea válida, pero vencerá antes del momento simulado.
        create_request(
            client=other_client,
            amount_minor=1000,
            minutes=1,
        )

        # La misma cuenta del vendedor no puede atender su solicitud.
        create_request(
            client=vendor,
            amount_minor=1000,
            minutes=5,
        )

        simulated_now = timezone.now() + timedelta(minutes=2)

        with patch(
            "apps.vendors.services.timezone.now",
            return_value=simulated_now,
        ):
            ids = set(
                eligible_conversion_requests(vendor=vendor)
                .values_list("pk", flat=True)
            )

        self.assertSetEqual(ids, {visible.pk})

    def test_inactive_vendor_profile_is_rejected(self):
        vendor = create_vendor(username="inactive_profile_vendor")
        VendorProfile.objects.filter(user=vendor).update(
            status=VendorProfile.Status.SUSPENDED
        )

        with self.assertRaises(ValidationError):
            list(eligible_conversion_requests(vendor=vendor))


class AssignConversionRequestTests(TestCase):
    def test_assignment_reserves_virtual_and_marks_in_progress(self):
        vendor = create_vendor(username="assign_vendor", virtual_minor=5000)
        client = create_client(username="assign_client")
        request = create_request(client=client, amount_minor=2500)

        assignment = assign_conversion_request(
            vendor=vendor,
            request_id=request.pk,
        )

        request.refresh_from_db()
        wallet = Wallet.objects.get(
            user=vendor,
            currency=Wallet.Currency.VIRTUAL,
        )
        self.assertEqual(request.status, ConversionRequest.Status.IN_PROGRESS)
        self.assertEqual(assignment.status, ConversionAssignment.Status.ACTIVE)
        self.assertEqual(wallet.available_minor, 2500)
        self.assertEqual(wallet.reserved_minor, 2500)

    def test_same_request_cannot_be_taken_twice(self):
        first_vendor = create_vendor(username="first_vendor", virtual_minor=5000)
        second_vendor = create_vendor(username="second_vendor", virtual_minor=5000)
        client = create_client(username="shared_client")
        request = create_request(client=client, amount_minor=2000)

        assign_conversion_request(vendor=first_vendor, request_id=request.pk)

        with self.assertRaises(ValidationError):
            assign_conversion_request(vendor=second_vendor, request_id=request.pk)

        self.assertEqual(
            ConversionAssignment.objects.filter(
                request=request,
                status=ConversionAssignment.Status.ACTIVE,
            ).count(),
            1,
        )
        second_wallet = Wallet.objects.get(
            user=second_vendor,
            currency=Wallet.Currency.VIRTUAL,
        )
        self.assertEqual(second_wallet.available_minor, 5000)
        self.assertEqual(second_wallet.reserved_minor, 0)

    def test_own_request_and_insufficient_inventory_are_rejected(self):
        own_vendor = create_vendor(username="own_vendor", virtual_minor=5000)
        own_request = create_request(client=own_vendor, amount_minor=1000)
        with self.assertRaises(ValidationError):
            assign_conversion_request(
                vendor=own_vendor,
                request_id=own_request.pk,
            )

        poor_vendor = create_vendor(username="poor_vendor", virtual_minor=500)
        client = create_client(username="large_request_client")
        large_request = create_request(client=client, amount_minor=1000)
        with self.assertRaises(ValidationError):
            assign_conversion_request(
                vendor=poor_vendor,
                request_id=large_request.pk,
            )

        large_request.refresh_from_db()
        self.assertEqual(large_request.status, ConversionRequest.Status.PENDING)


class VendorRequestViewTests(TestCase):
    def setUp(self):
        self.vendor = create_vendor(username="request_view_vendor", virtual_minor=5000)
        self.client.force_login(self.vendor)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = VENDOR
        session.save()

    def test_available_tab_shows_eligible_other_request_only(self):
        other = create_client(username="visible_other_client")
        visible = create_request(client=other, amount_minor=2000)
        own = create_request(client=self.vendor, amount_minor=1000)

        response = self.client.get(reverse("core:vendor_requests"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Solicitud #{visible.pk}")
        self.assertNotContains(response, f"Solicitud #{own.pk}")
        self.assertContains(response, "Tomar solicitud")
        self.assertNotContains(response, other.email)
        self.assertNotContains(response, other.document)

    def test_post_takes_request_and_redirects(self):
        other = create_client(username="post_request_client")
        request = create_request(client=other, amount_minor=2000)

        response = self.client.post(
            reverse("core:vendor_requests"),
            {"request_id": request.pk},
        )

        self.assertRedirects(response, reverse("core:vendor_requests"))
        self.assertTrue(
            ConversionAssignment.objects.filter(
                request=request,
                vendor__user=self.vendor,
                status=ConversionAssignment.Status.ACTIVE,
            ).exists()
        )

    def test_post_requires_csrf(self):
        other = create_client(username="csrf_request_client")
        request = create_request(client=other, amount_minor=1000)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.vendor)
        session = csrf_client.session
        session[ACTIVE_MODE_SESSION_KEY] = VENDOR
        session.save()

        response = csrf_client.post(
            reverse("core:vendor_requests"),
            {"request_id": request.pk},
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(ConversionAssignment.objects.filter(request=request).exists())
