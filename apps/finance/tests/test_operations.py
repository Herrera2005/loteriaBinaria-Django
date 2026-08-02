"""Pruebas de operaciones y agrupación visual de Finance."""

from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import CLIENT, VENDOR
from apps.accounts.tests.factories import create_user
from apps.finance.models import (
    Movement,
    TopUp,
    VirtualToRealConversion,
    Wallet,
    Withdrawal,
)
from apps.finance.services import (
    confirm_topup,
    confirm_withdrawal,
    convert_virtual_to_real,
    transfer_virtual,
)


class FinanceOperationServiceTests(TestCase):
    def setUp(self):
        self.user = create_user(
            username="finance_ops",
            email="finance.ops@example.test",
            document="FIN-OPS",
            roles=(CLIENT,),
        )
        self.other = create_user(
            username="finance_other",
            email="finance.other@example.test",
            document="FIN-OTHER",
            roles=(CLIENT,),
        )

    def wallet(self, user, currency):
        return Wallet.objects.get(user=user, currency=currency)

    def test_topup_is_one_to_one_and_idempotent(self):
        operation_id = uuid.uuid4()
        first, created = confirm_topup(
            user=self.user,
            amount_minor=10000,
            operation_id=operation_id,
        )
        second, created_again = confirm_topup(
            user=self.user,
            amount_minor=10000,
            operation_id=operation_id,
        )

        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(
            self.wallet(self.user, Wallet.Currency.REAL).available_minor,
            10000,
        )
        self.assertEqual(
            Movement.objects.filter(operation_id=operation_id).count(),
            1,
        )

    def test_conversion_uses_exact_90_10(self):
        Wallet.objects.filter(
            user=self.user,
            currency=Wallet.Currency.VIRTUAL,
        ).update(available_minor=50000)

        operation, created = convert_virtual_to_real(
            user=self.user,
            gross_virtual_minor=50000,
            operation_id=uuid.uuid4(),
        )

        self.assertTrue(created)
        self.assertEqual(operation.fee_virtual_minor, 5000)
        self.assertEqual(operation.net_real_minor, 45000)
        self.assertEqual(
            self.wallet(self.user, Wallet.Currency.VIRTUAL).available_minor,
            0,
        )
        self.assertEqual(
            self.wallet(self.user, Wallet.Currency.REAL).available_minor,
            45000,
        )

    def test_conversion_rejects_insufficient_balance_without_effects(self):
        with self.assertRaises(ValidationError):
            convert_virtual_to_real(
                user=self.user,
                gross_virtual_minor=100,
                operation_id=uuid.uuid4(),
            )

        self.assertEqual(VirtualToRealConversion.objects.count(), 0)
        self.assertEqual(Movement.objects.count(), 0)

    def test_transfer_moves_only_virtual(self):
        Wallet.objects.filter(
            user=self.user,
            currency=Wallet.Currency.VIRTUAL,
        ).update(available_minor=2500)

        operation_id = uuid.uuid4()
        transfer_virtual(
            sender=self.user,
            recipient_identifier=self.other.email,
            amount_minor=1000,
            operation_id=operation_id,
        )

        self.assertEqual(
            self.wallet(self.user, Wallet.Currency.VIRTUAL).available_minor,
            1500,
        )
        self.assertEqual(
            self.wallet(self.other, Wallet.Currency.VIRTUAL).available_minor,
            1000,
        )
        self.assertEqual(
            Movement.objects.filter(operation_id=operation_id).count(),
            2,
        )

    def test_transfer_rejects_self(self):
        with self.assertRaises(ValidationError):
            transfer_virtual(
                sender=self.user,
                recipient_identifier=self.user.username,
                amount_minor=100,
                operation_id=uuid.uuid4(),
            )

    def test_withdrawal_has_no_second_fee(self):
        Wallet.objects.filter(
            user=self.user,
            currency=Wallet.Currency.REAL,
        ).update(available_minor=45000)

        confirm_withdrawal(
            user=self.user,
            amount_minor=45000,
            operation_id=uuid.uuid4(),
        )

        self.assertEqual(
            self.wallet(self.user, Wallet.Currency.REAL).available_minor,
            0,
        )
        self.assertEqual(Withdrawal.objects.get().amount_minor, 45000)


class FinanceOperationViewTests(TestCase):
    def setUp(self):
        self.user = create_user(
            username="finance_web",
            email="finance.web@example.test",
            document="FIN-WEB",
            roles=(CLIENT,),
        )
        self.client.force_login(self.user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = CLIENT
        session.save()

    def test_grouped_operation_pages_open_for_client_mode(self):
        for name in (
            "finance:real_operations",
            "finance:wallet_conversion",
            "finance:virtual_transfer",
        ):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_real_operations_show_both_wallet_balances(self):
        Wallet.objects.filter(
            user=self.user,
            currency=Wallet.Currency.REAL,
        ).update(available_minor=12345, reserved_minor=500)
        Wallet.objects.filter(
            user=self.user,
            currency=Wallet.Currency.VIRTUAL,
        ).update(available_minor=250, reserved_minor=25)

        response = self.client.get(reverse("finance:real_operations"))

        self.assertContains(response, "$ 123.45")
        self.assertContains(response, "$ 5.00")
        self.assertContains(response, "V 2.50")
        self.assertContains(response, "V 0.25")

    def test_real_operations_switch_to_withdrawal_tab(self):
        response = self.client.get(
            reverse("finance:real_operations"),
            {"tab": "withdrawal"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Retiro académico")
        self.assertContains(response, 'name="action" value="withdrawal"')

    def test_wallet_conversion_explains_real_to_virtual_request(self):
        response = self.client.get(
            reverse("finance:wallet_conversion"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "REAL → VIRTUAL")
        self.assertContains(response, "Solicitar REAL → VIRTUAL")
        self.assertContains(
            response,
            "Un vendedor elegible atenderá la solicitud",
        )
        self.assertContains(
            response,
            "se acreditará cuando la operación sea completada",
        )
        self.assertContains(
            response,
            "saldo bloqueado",
        )

    def test_real_to_virtual_tab_does_not_create_request(self):
        from apps.vendors.models import ConversionRequest

        response = self.client.get(
            reverse("finance:wallet_conversion"),
            {"tab": "real-to-virtual"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ConversionRequest.objects.count(), 0)

    def test_topup_post_creates_operation_and_redirects(self):
        response = self.client.post(
            reverse("finance:real_operations"),
            {
                "action": "topup",
                "topup-amount": "10.00",
                "topup-operation_id": str(uuid.uuid4()),
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('finance:wallet_detail')}?tab=movements",
        )
        self.assertEqual(TopUp.objects.count(), 1)

    def test_withdrawal_post_uses_its_own_prefixed_form(self):
        Wallet.objects.filter(
            user=self.user,
            currency=Wallet.Currency.REAL,
        ).update(available_minor=1000)

        response = self.client.post(
            reverse("finance:real_operations"),
            {
                "action": "withdrawal",
                "withdrawal-amount": "5.00",
                "withdrawal-operation_id": str(uuid.uuid4()),
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('finance:wallet_detail')}?tab=movements",
        )
        self.assertEqual(Withdrawal.objects.count(), 1)

    def test_vendor_mode_receives_403(self):
        vendor = create_user(
            username="finance_vendor",
            email="finance.vendor@example.test",
            document="FIN-VND",
            roles=(VENDOR,),
        )
        self.client.force_login(vendor)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = VENDOR
        session.save()

        for name in (
            "finance:real_operations",
            "finance:wallet_conversion",
            "finance:virtual_transfer",
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    self.client.get(reverse(name)).status_code,
                    403,
                )

    def test_topup_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        session = csrf_client.session
        session[ACTIVE_MODE_SESSION_KEY] = CLIENT
        session.save()

        response = csrf_client.post(
            reverse("finance:real_operations"),
            {
                "action": "topup",
                "topup-amount": "10.00",
                "topup-operation_id": str(uuid.uuid4()),
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(TopUp.objects.count(), 0)

    def test_legacy_operation_urls_redirect_to_grouped_pages(self):
        expected = {
            "finance:topup": (
                "finance:real_operations",
                "topup",
            ),
            "finance:withdrawal": (
                "finance:real_operations",
                "withdrawal",
            ),
            "finance:conversion": (
                "finance:wallet_conversion",
                "virtual-to-real",
            ),
        }

        for old_name, (new_name, tab) in expected.items():
            with self.subTest(old_name=old_name):
                response = self.client.get(reverse(old_name))
                self.assertRedirects(
                    response,
                    f"{reverse(new_name)}?tab={tab}",
                )
