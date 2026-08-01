"""Pruebas P-28A de Wallet, Movement, provisión y admin read-only."""

from __future__ import annotations

import uuid
from io import StringIO

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, models, transaction
from django.test import RequestFactory, TestCase

from apps.accounts.models import User
from apps.accounts.roles import CLIENT, VENDOR
from apps.accounts.tests.factories import create_user
from apps.finance.admin import MovementAdmin, WalletAdmin
from apps.finance.models import Movement, Wallet
from apps.finance.services import ensure_user_wallets


def create_client_user(**overrides):
    defaults = {
        "username": "finance_client",
        "email": "finance.client@example.test",
        "document": "FIN-CLIENT-001",
        "roles": (CLIENT,),
    }
    defaults.update(overrides)
    return create_user(**defaults)


def get_wallet(user, currency):
    return Wallet.objects.get(user=user, currency=currency)


def create_movement(
    *,
    wallet,
    operation_id=None,
    movement_type=Movement.Type.TOP_UP,
    direction=Movement.Direction.CREDIT,
    amount_minor=1000,
    balance_after_minor=1000,
):
    return Movement.objects.create(
        wallet=wallet,
        operation_id=operation_id or uuid.uuid4(),
        type=movement_type,
        direction=direction,
        amount_minor=amount_minor,
        balance_after_minor=balance_after_minor,
        description="Movimiento académico de prueba.",
    )


class WalletModelTests(TestCase):
    def test_role_assignment_provisions_real_and_virtual_wallets(self):
        user = create_client_user()

        self.assertEqual(user.wallets.count(), 2)
        self.assertSetEqual(
            set(user.wallets.values_list("currency", flat=True)),
            {Wallet.Currency.REAL, Wallet.Currency.VIRTUAL},
        )

    def test_wallet_service_is_idempotent(self):
        user = create_client_user()

        first = ensure_user_wallets(user)
        second = ensure_user_wallets(user)

        self.assertEqual(user.wallets.count(), 2)
        self.assertEqual(
            first[Wallet.Currency.REAL].pk,
            second[Wallet.Currency.REAL].pk,
        )
        self.assertEqual(
            first[Wallet.Currency.VIRTUAL].pk,
            second[Wallet.Currency.VIRTUAL].pk,
        )

    def test_unsaved_user_is_rejected_by_wallet_service(self):
        user = User(
            username="unsaved_finance",
            email="unsaved.finance@example.test",
            document="FIN-UNSAVED-001",
        )

        with self.assertRaises(ValidationError):
            ensure_user_wallets(user)

    def test_suspended_user_receives_suspended_wallets(self):
        user = create_user(
            username="finance_suspended",
            email="finance.suspended@example.test",
            document="FIN-SUSP-001",
            status=User.Status.SUSPENDED,
        )

        wallets = ensure_user_wallets(user)

        self.assertEqual(
            wallets[Wallet.Currency.REAL].status,
            Wallet.Status.SUSPENDED,
        )
        self.assertEqual(
            wallets[Wallet.Currency.VIRTUAL].status,
            Wallet.Status.SUSPENDED,
        )

    def test_wallet_is_unique_per_user_and_currency(self):
        user = create_client_user()

        with self.assertRaises(IntegrityError), transaction.atomic():
            Wallet.objects.create(
                user=user,
                currency=Wallet.Currency.REAL,
            )

    def test_wallet_money_fields_use_big_integer_minor_units(self):
        for field_name in ("available_minor", "reserved_minor"):
            with self.subTest(field_name=field_name):
                field = Wallet._meta.get_field(field_name)
                self.assertIsInstance(field, models.BigIntegerField)
                self.assertNotIsInstance(field, models.FloatField)
                self.assertNotIsInstance(field, models.DecimalField)

    def test_wallet_rejects_negative_balances(self):
        wallet = Wallet(
            user=create_user(
                username="negative_wallet",
                email="negative.wallet@example.test",
                document="FIN-NEG-001",
            ),
            currency=Wallet.Currency.REAL,
            available_minor=-1,
            reserved_minor=0,
        )

        with self.assertRaises(ValidationError) as context:
            wallet.full_clean()

        self.assertIn("available_minor", context.exception.message_dict)

    def test_wallet_database_checks_reject_negative_update(self):
        wallet = get_wallet(create_client_user(), Wallet.Currency.REAL)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Wallet.objects.filter(pk=wallet.pk).update(
                reserved_minor=-1,
            )

    def test_wallet_protects_its_user(self):
        user = create_client_user()
        field = Wallet._meta.get_field("user")

        self.assertIs(field.remote_field.on_delete, models.PROTECT)
        with self.assertRaises(models.ProtectedError):
            user.delete()

    def test_backfill_command_creates_missing_wallets_and_is_idempotent(self):
        user = create_user(
            username="backfill_user",
            email="backfill.user@example.test",
            document="FIN-BACKFILL-001",
        )
        self.assertFalse(user.wallets.exists())

        call_command("backfill_wallets", stdout=StringIO())
        call_command("backfill_wallets", stdout=StringIO())

        self.assertEqual(user.wallets.count(), 2)
        self.assertEqual(Wallet.objects.filter(user=user).count(), 2)

    def test_assigning_a_second_role_does_not_duplicate_wallets(self):
        user = create_client_user()
        from django.contrib.auth.models import Group

        vendor_group, _ = Group.objects.get_or_create(name=VENDOR)
        user.groups.add(vendor_group)

        self.assertEqual(user.wallets.count(), 2)


class MovementModelTests(TestCase):
    def setUp(self):
        self.user = create_client_user()
        self.real_wallet = get_wallet(self.user, Wallet.Currency.REAL)
        self.virtual_wallet = get_wallet(self.user, Wallet.Currency.VIRTUAL)

    def test_movement_money_fields_use_big_integer_minor_units(self):
        for field_name in ("amount_minor", "balance_after_minor"):
            with self.subTest(field_name=field_name):
                field = Movement._meta.get_field(field_name)
                self.assertIsInstance(field, models.BigIntegerField)
                self.assertNotIsInstance(field, models.FloatField)
                self.assertNotIsInstance(field, models.DecimalField)

    def test_movement_uses_protected_wallet_relation(self):
        field = Movement._meta.get_field("wallet")
        self.assertIs(field.remote_field.on_delete, models.PROTECT)

        create_movement(wallet=self.real_wallet)
        with self.assertRaises(models.ProtectedError):
            self.real_wallet.delete()

    def test_operation_id_correlates_multiple_movements(self):
        operation_id = uuid.uuid4()

        create_movement(
            wallet=self.real_wallet,
            operation_id=operation_id,
        )
        create_movement(
            wallet=self.virtual_wallet,
            operation_id=operation_id,
            movement_type=Movement.Type.VIRTUAL_TO_REAL,
            direction=Movement.Direction.DEBIT,
            amount_minor=1000,
            balance_after_minor=0,
        )

        self.assertEqual(
            Movement.objects.filter(operation_id=operation_id).count(),
            2,
        )

    def test_movement_rejects_non_positive_amount(self):
        movement = Movement(
            wallet=self.real_wallet,
            type=Movement.Type.TOP_UP,
            direction=Movement.Direction.CREDIT,
            amount_minor=0,
            balance_after_minor=0,
        )

        with self.assertRaises(ValidationError) as context:
            movement.full_clean()

        self.assertIn("amount_minor", context.exception.message_dict)

    def test_existing_movement_cannot_be_saved_again(self):
        movement = create_movement(wallet=self.real_wallet)
        movement.description = "Intento de reescritura"

        with self.assertRaises(ValidationError):
            movement.save()

    def test_movement_cannot_be_deleted_individually_or_in_bulk(self):
        movement = create_movement(wallet=self.real_wallet)

        with self.assertRaises(ValidationError):
            movement.delete()

        with self.assertRaises(ValidationError):
            Movement.objects.filter(pk=movement.pk).delete()

    def test_movement_cannot_be_updated_in_bulk(self):
        movement = create_movement(wallet=self.real_wallet)

        with self.assertRaises(ValidationError):
            Movement.objects.filter(pk=movement.pk).update(
                description="Intento masivo"
            )

        with self.assertRaises(ValidationError):
            Movement.objects.bulk_update(
                [movement],
                ["description"],
            )


class FinanceAdminReadOnlyTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/admin/")
        self.request.user = create_user(
            username="finance_admin",
            email="finance.admin@example.test",
            document="FIN-ADMIN-001",
            is_staff=True,
            is_superuser=True,
        )

    def test_wallet_admin_is_read_only(self):
        model_admin = WalletAdmin(Wallet, admin.site)

        self.assertFalse(model_admin.has_add_permission(self.request))
        self.assertFalse(model_admin.has_change_permission(self.request))
        self.assertFalse(model_admin.has_delete_permission(self.request))
        self.assertTrue(model_admin.has_view_permission(self.request))

    def test_movement_admin_is_read_only(self):
        model_admin = MovementAdmin(Movement, admin.site)

        self.assertFalse(model_admin.has_add_permission(self.request))
        self.assertFalse(model_admin.has_change_permission(self.request))
        self.assertFalse(model_admin.has_delete_permission(self.request))
        self.assertTrue(model_admin.has_view_permission(self.request))
