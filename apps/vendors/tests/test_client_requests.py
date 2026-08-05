"""Pruebas P-34A de solicitudes REAL → VIRTUAL del Cliente."""

from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import CLIENT, VENDOR
from apps.accounts.tests.factories import create_user
from apps.finance.models import Movement, Wallet
from apps.vendors.models import ConversionRequest
from apps.vendors.services import create_conversion_request


class ConversionRequestServiceTests(TestCase):
    def setUp(self):
        self.client_user = create_user(
            username="request_client",
            email="request.client@example.test",
            document="REQ-CLIENT-001",
            roles=(CLIENT,),
        )
        self.real_wallet = Wallet.objects.get(
            user=self.client_user,
            currency=Wallet.Currency.REAL,
        )
        Wallet.objects.filter(pk=self.real_wallet.pk).update(
            available_minor=10_000,
        )

    def test_create_request_reserves_real_without_crediting_virtual(self):
        operation_id = uuid.uuid4()

        request_obj, created = create_conversion_request(
            client=self.client_user,
            amount_minor=2_500,
            operation_id=operation_id,
        )

        self.assertTrue(created)
        self.real_wallet.refresh_from_db()
        virtual_wallet = Wallet.objects.get(
            user=self.client_user,
            currency=Wallet.Currency.VIRTUAL,
        )
        self.assertEqual(self.real_wallet.available_minor, 7_500)
        self.assertEqual(self.real_wallet.reserved_minor, 2_500)
        self.assertEqual(virtual_wallet.available_minor, 0)
        self.assertEqual(request_obj.status, ConversionRequest.Status.PENDING)
        self.assertEqual(
            Movement.objects.filter(operation_id=operation_id).count(),
            1,
        )

    def test_request_is_idempotent(self):
        operation_id = uuid.uuid4()

        first, first_created = create_conversion_request(
            client=self.client_user,
            amount_minor=2_000,
            operation_id=operation_id,
        )
        second, second_created = create_conversion_request(
            client=self.client_user,
            amount_minor=2_000,
            operation_id=operation_id,
        )

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first.pk, second.pk)
        self.real_wallet.refresh_from_db()
        self.assertEqual(self.real_wallet.available_minor, 8_000)
        self.assertEqual(self.real_wallet.reserved_minor, 2_000)
        self.assertEqual(ConversionRequest.objects.count(), 1)
        self.assertEqual(Movement.objects.count(), 1)

    def test_insufficient_balance_rolls_back_everything(self):
        with self.assertRaises(ValidationError):
            create_conversion_request(
                client=self.client_user,
                amount_minor=20_000,
                operation_id=uuid.uuid4(),
            )

        self.real_wallet.refresh_from_db()
        self.assertEqual(self.real_wallet.available_minor, 10_000)
        self.assertEqual(self.real_wallet.reserved_minor, 0)
        self.assertFalse(ConversionRequest.objects.exists())
        self.assertFalse(Movement.objects.exists())


class ConversionRequestClientViewTests(TestCase):
    def setUp(self):
        self.user = create_user(
            username="request_view_client",
            email="request.view@example.test",
            document="REQ-VIEW-001",
            roles=(CLIENT,),
        )
        Wallet.objects.filter(
            user=self.user,
            currency=Wallet.Currency.REAL,
        ).update(available_minor=10_000)
        self.client.force_login(self.user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = CLIENT
        session.save()

    def test_real_to_virtual_tab_renders_form_and_balances(self):
        response = self.client.get(
            reverse("finance:wallet_conversion"),
            {"tab": "real-to-virtual"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Solicitar REAL → VIRTUAL")
        self.assertContains(response, "$ 100.00")
        self.assertContains(response, "Crear solicitud")

    def test_post_creates_request_and_redirects_to_own_detail(self):
        operation_id = uuid.uuid4()
        response = self.client.post(
            reverse("finance:wallet_conversion"),
            {
                "action": "real-to-virtual",
                "request-amount": "25.00",
                "request-operation_id": str(operation_id),
            },
        )

        request_obj = ConversionRequest.objects.get(operation_id=operation_id)
        self.assertRedirects(
            response,
            reverse(
                "vendors:client_conversionrequest_detail",
                args=(request_obj.pk,),
            ),
        )

    def test_client_only_sees_own_requests(self):
        own, _ = create_conversion_request(
            client=self.user,
            amount_minor=1_000,
            operation_id=uuid.uuid4(),
        )
        other = create_user(
            username="other_request_client",
            email="other.request@example.test",
            document="REQ-OTHER-001",
            roles=(CLIENT,),
        )
        Wallet.objects.filter(
            user=other,
            currency=Wallet.Currency.REAL,
        ).update(available_minor=5_000)
        foreign, _ = create_conversion_request(
            client=other,
            amount_minor=1_000,
            operation_id=uuid.uuid4(),
        )

        listing = self.client.get(
            reverse("vendors:client_conversionrequest_list")
        )
        forbidden_detail = self.client.get(
            reverse(
                "vendors:client_conversionrequest_detail",
                args=(foreign.pk,),
            )
        )

        self.assertContains(listing, str(own.operation_id))
        self.assertNotContains(listing, str(foreign.operation_id))
        self.assertEqual(forbidden_detail.status_code, 404)

    def test_vendor_mode_cannot_create_or_read_client_requests(self):
        vendor = create_user(
            username="request_vendor",
            email="request.vendor@example.test",
            document="REQ-VENDOR-001",
            roles=(VENDOR,),
        )
        self.client.force_login(vendor)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = VENDOR
        session.save()

        self.assertEqual(
            self.client.get(
                reverse("vendors:client_conversionrequest_list")
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse("finance:wallet_conversion"),
                {"tab": "real-to-virtual"},
            ).status_code,
            403,
        )

    def test_request_post_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        session = csrf_client.session
        session[ACTIVE_MODE_SESSION_KEY] = CLIENT
        session.save()

        response = csrf_client.post(
            reverse("finance:wallet_conversion"),
            {
                "action": "real-to-virtual",
                "request-amount": "10.00",
                "request-operation_id": str(uuid.uuid4()),
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(ConversionRequest.objects.exists())
