from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import CLIENT, VENDOR
from apps.accounts.tests.factories import create_user
from apps.vendors.models import VendorProfile

from apps.finance.models import (
    Movement,
    VendorInventoryPurchase,
    Wallet,
)
from apps.finance.services import purchase_vendor_inventory


def create_vendor(*, profile_status=VendorProfile.Status.ACTIVE):
    user = create_user(
        username="vendor_finance",
        email="vendor.finance@example.test",
        document="VENDOR-FINANCE",
        roles=(VENDOR,),
    )
    VendorProfile.objects.create(user=user, status=profile_status)
    return user


def wallet(user, currency):
    return Wallet.objects.get(user=user, currency=currency)


class VendorInventoryPurchaseServiceTests(TestCase):
    def setUp(self):
        self.vendor = create_vendor()
        self.real = wallet(self.vendor, Wallet.Currency.REAL)
        self.virtual = wallet(self.vendor, Wallet.Currency.VIRTUAL)
        Wallet.objects.filter(pk=self.real.pk).update(available_minor=15000)

    def test_purchase_100_virtual_costs_90_real_exactly(self):
        operation_id = uuid.uuid4()

        purchase, created = purchase_vendor_inventory(
            vendor=self.vendor,
            virtual_minor=10000,
            operation_id=operation_id,
        )

        self.assertTrue(created)
        self.assertEqual(purchase.amount_minor, 10000)
        self.assertEqual(purchase.cost_real_minor, 9000)
        self.real.refresh_from_db()
        self.virtual.refresh_from_db()
        self.assertEqual(self.real.available_minor, 6000)
        self.assertEqual(self.virtual.available_minor, 10000)
        self.assertEqual(
            Movement.objects.filter(operation_id=operation_id).count(),
            2,
        )

    def test_purchase_rejects_fractional_virtual_unit(self):
        with self.assertRaises(ValidationError):
            purchase_vendor_inventory(
                vendor=self.vendor,
                virtual_minor=50,
                operation_id=uuid.uuid4(),
            )

        self.real.refresh_from_db()
        self.virtual.refresh_from_db()
        self.assertEqual(self.real.available_minor, 15000)
        self.assertEqual(self.virtual.available_minor, 0)

    def test_insufficient_real_rolls_back(self):
        with self.assertRaises(ValidationError):
            purchase_vendor_inventory(
                vendor=self.vendor,
                virtual_minor=20000,
                operation_id=uuid.uuid4(),
            )

        self.assertEqual(VendorInventoryPurchase.objects.count(), 0)
        self.assertEqual(Movement.objects.count(), 0)

    def test_operation_id_is_idempotent(self):
        operation_id = uuid.uuid4()
        first, first_created = purchase_vendor_inventory(
            vendor=self.vendor,
            virtual_minor=10000,
            operation_id=operation_id,
        )
        second, second_created = purchase_vendor_inventory(
            vendor=self.vendor,
            virtual_minor=10000,
            operation_id=operation_id,
        )

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(VendorInventoryPurchase.objects.count(), 1)
        self.assertEqual(Movement.objects.count(), 2)

    def test_active_vendor_profile_is_required(self):
        blocked = create_user(
            username="vendor_without_profile",
            email="vendor.without.profile@example.test",
            document="VENDOR-NO-PROFILE",
            roles=(VENDOR,),
        )
        with self.assertRaises(ValidationError):
            purchase_vendor_inventory(
                vendor=blocked,
                virtual_minor=10000,
                operation_id=uuid.uuid4(),
            )


class VendorFinanceViewTests(TestCase):
    def setUp(self):
        self.vendor = create_vendor()
        self.client.force_login(self.vendor)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = VENDOR
        session.save()

    def test_vendor_navigation_has_separate_sections(self):
        response = self.client.get(reverse("core:vendor_dashboard"))

        self.assertContains(response, "Operaciones REAL")
        self.assertContains(response, "Monedas e inventario")
        self.assertContains(response, "Solicitudes")
        self.assertContains(
            response,
            reverse("finance:vendor_real_operations"),
        )
        self.assertContains(
            response,
            reverse("finance:vendor_currency_operations"),
        )
        self.assertContains(response, reverse("core:vendor_requests"))

    def test_vendor_pages_open_and_show_wallet_reference(self):
        for url_name in (
            "finance:vendor_real_operations",
            "finance:vendor_currency_operations",
            "finance:vendor_inventory",
            "core:vendor_requests",
        ):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

    def test_client_mode_cannot_open_vendor_finance(self):
        client_user = create_user(
            username="client_denied_vendor_finance",
            email="client.denied@example.test",
            document="CLIENT-DENIED-VENDOR-FIN",
            roles=(CLIENT,),
        )
        self.client.force_login(client_user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = CLIENT
        session.save()

        response = self.client.get(
            reverse("finance:vendor_currency_operations")
        )
        self.assertEqual(response.status_code, 403)

    def test_wholesale_post_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.vendor)
        session = csrf_client.session
        session[ACTIVE_MODE_SESSION_KEY] = VENDOR
        session.save()

        response = csrf_client.post(
            reverse("finance:vendor_currency_operations"),
            {
                "action": "wholesale",
                "wholesale-amount": "100.00",
                "wholesale-operation_id": str(uuid.uuid4()),
            },
        )
        self.assertEqual(response.status_code, 403)
