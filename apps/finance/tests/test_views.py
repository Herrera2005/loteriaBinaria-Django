"""Pruebas P-28 de propiedad, filtros, paginación y métodos HTTP."""

from __future__ import annotations

from django.test import TestCase
from django.urls import reverse

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import ADMINISTRATOR, CLIENT, VENDOR
from apps.accounts.tests.factories import create_user
from apps.finance.models import Movement, Wallet


class FinanceReadOnlyViewTests(TestCase):
    def activate(self, user, mode):
        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = mode
        session.save()

    def create_movement(
        self,
        *,
        user,
        currency=Wallet.Currency.REAL,
        movement_type=Movement.Type.TOP_UP,
        direction=Movement.Direction.CREDIT,
        amount_minor=100,
        balance_after_minor=100,
        description="Movimiento de prueba",
    ):
        wallet = Wallet.objects.get(user=user, currency=currency)
        return Movement.objects.create(
            wallet=wallet,
            type=movement_type,
            direction=direction,
            amount_minor=amount_minor,
            balance_after_minor=balance_after_minor,
            description=description,
        )

    def test_anonymous_user_is_redirected_to_login(self):
        for name in ("finance:wallet_detail", "finance:movement_list"):
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{reverse('accounts:login')}?next={url}",
                )

    def test_user_without_active_mode_is_redirected_to_selector(self):
        user = create_user(roles=(CLIENT,))
        self.client.force_login(user)

        response = self.client.get(reverse("finance:wallet_detail"))

        self.assertRedirects(response, reverse("accounts:choose_mode"))

    def test_all_assigned_active_modes_can_open_own_finance_pages(self):
        for index, mode in enumerate((CLIENT, VENDOR, ADMINISTRATOR), start=1):
            user = create_user(
                username=f"finance_mode_{index}",
                email=f"finance.mode.{index}@example.test",
                document=f"FIN-MODE-{index:03d}",
                roles=(mode,),
            )
            self.activate(user, mode)

            with self.subTest(mode=mode):
                wallet_response = self.client.get(
                    reverse("finance:wallet_detail")
                )
                movement_response = self.client.get(
                    reverse("finance:movement_list")
                )
                self.assertEqual(wallet_response.status_code, 200)
                self.assertEqual(movement_response.status_code, 200)

            self.client.logout()

    def test_wallet_page_only_shows_current_user_wallets(self):
        owner = create_user(
            username="wallet_owner",
            email="wallet.owner@example.test",
            document="WALLET-OWNER-001",
            roles=(CLIENT,),
        )
        other = create_user(
            username="wallet_other",
            email="wallet.other@example.test",
            document="WALLET-OTHER-001",
            roles=(CLIENT,),
        )
        Wallet.objects.filter(
            user=owner,
            currency=Wallet.Currency.REAL,
        ).update(available_minor=1234)
        Wallet.objects.filter(
            user=other,
            currency=Wallet.Currency.REAL,
        ).update(available_minor=987654)
        self.activate(owner, CLIENT)

        response = self.client.get(
            reverse("finance:wallet_detail"),
            {"user": other.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "$ 12.34")
        self.assertNotContains(response, "$ 9,876.54")
        self.assertEqual(
            {item["wallet"].user_id for item in response.context["wallet_cards"]},
            {owner.pk},
        )

    def test_wallet_get_does_not_create_missing_wallets(self):
        user = create_user(
            username="wallet_missing",
            email="wallet.missing@example.test",
            document="WALLET-MISSING-001",
            roles=(CLIENT,),
        )
        Wallet.objects.filter(user=user).delete()
        self.activate(user, CLIENT)

        response = self.client.get(reverse("finance:wallet_detail"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Wallet.objects.filter(user=user).count(), 0)
        self.assertContains(response, "No hay wallets disponibles")

    def test_wallet_post_is_not_allowed(self):
        user = create_user(roles=(CLIENT,))
        self.activate(user, CLIENT)

        response = self.client.post(reverse("finance:wallet_detail"), {})

        self.assertEqual(response.status_code, 405)

    def test_wallet_pk_route_does_not_exist(self):
        user = create_user(roles=(CLIENT,))
        other = create_user(
            username="wallet_pk_other",
            email="wallet.pk.other@example.test",
            document="WALLET-PK-OTHER",
            roles=(CLIENT,),
        )
        self.activate(user, CLIENT)

        response = self.client.get(f"/finance/wallets/{other.pk}/")

        self.assertEqual(response.status_code, 404)

    def test_movement_list_only_shows_current_user_movements(self):
        owner = create_user(
            username="movement_owner",
            email="movement.owner@example.test",
            document="MOVE-OWNER-001",
            roles=(CLIENT,),
        )
        other = create_user(
            username="movement_other",
            email="movement.other@example.test",
            document="MOVE-OTHER-001",
            roles=(CLIENT,),
        )
        self.create_movement(
            user=owner,
            description="MOVIMIENTO-PROPIO-ÚNICO",
        )
        self.create_movement(
            user=other,
            description="MOVIMIENTO-AJENO-SECRETO",
        )
        self.activate(owner, CLIENT)

        response = self.client.get(
            reverse("finance:movement_list"),
            {"user": other.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MOVIMIENTO-PROPIO-ÚNICO")
        self.assertNotContains(response, "MOVIMIENTO-AJENO-SECRETO")

    def test_movement_filters_use_valid_backend_choices(self):
        user = create_user(roles=(CLIENT,))
        self.create_movement(
            user=user,
            currency=Wallet.Currency.REAL,
            movement_type=Movement.Type.TOP_UP,
            direction=Movement.Direction.CREDIT,
            description="REAL-CREDIT-FILTER",
        )
        self.create_movement(
            user=user,
            currency=Wallet.Currency.VIRTUAL,
            movement_type=Movement.Type.TICKET_PURCHASE,
            direction=Movement.Direction.DEBIT,
            description="VIRTUAL-DEBIT-FILTER",
        )
        self.activate(user, CLIENT)

        response = self.client.get(
            reverse("finance:movement_list"),
            {
                "currency": Wallet.Currency.VIRTUAL,
                "type": Movement.Type.TICKET_PURCHASE,
                "direction": Movement.Direction.DEBIT,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VIRTUAL-DEBIT-FILTER")
        self.assertNotContains(response, "REAL-CREDIT-FILTER")

    def test_movement_list_is_paginated(self):
        user = create_user(roles=(CLIENT,))
        for index in range(16):
            self.create_movement(
                user=user,
                amount_minor=index + 1,
                balance_after_minor=index + 1,
                description=f"PAGE-MOVEMENT-{index:02d}",
            )
        self.activate(user, CLIENT)

        first_page = self.client.get(reverse("finance:movement_list"))
        second_page = self.client.get(
            reverse("finance:movement_list"),
            {"page": 2},
        )

        self.assertEqual(len(first_page.context["movement_rows"]), 15)
        self.assertEqual(len(second_page.context["movement_rows"]), 1)
        self.assertTrue(first_page.context["is_paginated"])

    def test_movement_post_is_not_allowed(self):
        user = create_user(roles=(CLIENT,))
        self.activate(user, CLIENT)

        response = self.client.post(reverse("finance:movement_list"), {})

        self.assertEqual(response.status_code, 405)
