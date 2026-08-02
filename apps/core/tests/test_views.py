from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import ADMINISTRATOR, CLIENT, VENDOR
from apps.accounts.tests.factories import create_user
from apps.core.models import AuditEvent
from apps.finance.models import Movement, Wallet
from apps.lottery.models import LotteryProduct
from apps.vendors.models import (
    ConversionAssignment,
    ConversionRequest,
    VendorProfile,
)


class PublicAndDashboardViewTests(TestCase):
    def test_start_redirects_anonymous_user_to_public_home(self):
        response = self.client.get(reverse("core:start"))

        self.assertRedirects(
            response,
            reverse("core:home"),
        )


    def test_start_redirects_authenticated_user_without_mode_to_selector(self):
        user = create_user(
            roles=(CLIENT, VENDOR),
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:start"))

        self.assertRedirects(
            response,
            reverse("accounts:choose_mode"),
        )


    def test_start_redirects_each_active_mode_to_its_dashboard(self):
        cases = (
            (CLIENT, "core:client_dashboard"),
            (VENDOR, "core:vendor_dashboard"),
            (ADMINISTRATOR, "core:admin_dashboard"),
        )

        for mode, expected_route in cases:
            with self.subTest(mode=mode):
                self.client.logout()

                user = create_user(
                    username=f"start_{mode.lower()}",
                    email=f"start.{mode.lower()}@example.test",
                    document=f"START-{mode}",
                    roles=(mode,),
                )

                self.client.force_login(user)

                session = self.client.session
                session[ACTIVE_MODE_SESSION_KEY] = mode
                session.save()

                response = self.client.get(reverse("core:start"))

                self.assertRedirects(
                    response,
                    reverse(expected_route),
                )


    def test_navigation_shows_only_links_allowed_for_client_mode(self):
        user = create_user(
            username="nav_client",
            email="nav-client@example.test",
            document="NAV-CLIENT",
            roles=(CLIENT,),
        )

        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = CLIENT
        session.save()

        response = self.client.get(reverse("core:client_dashboard"))

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            reverse("core:client_dashboard"),
        )
        self.assertContains(
            response,
            reverse("finance:wallet_detail"),
        )
        self.assertContains(response, "Billeteras y movimientos")
        self.assertContains(
            response,
            reverse("finance:real_operations"),
        )
        self.assertContains(
            response,
            reverse("finance:wallet_conversion"),
        )
        self.assertContains(
            response,
            reverse("vendors:client_conversionrequest_list"),
        )
        self.assertContains(
            response,
            reverse("finance:virtual_transfer"),
        )

        self.assertContains(response, "Mis solicitudes")

        self.assertNotContains(
            response,
            f'href="{reverse("vendors:vendorprofile_list")}"',
        )
        self.assertNotContains(
            response,
            f'href="{reverse("vendors:vendorprofile_create")}"',
        )
        self.assertNotContains(
            response,
            f'href="{reverse("vendors:conversionrequest_list")}"',
        )
                
        self.assertNotContains(
            response,
            reverse("core:admin_dashboard"),
        )
        self.assertNotContains(
            response,
            reverse("core:vendor_dashboard"),
        )

    def activate(self, user, mode):
        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = mode
        session.save()

    def test_home_is_public_and_uses_expected_template(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")
        self.assertContains(response, "Octal")
        self.assertContains(response, "Decimal")
        self.assertContains(response, "Hexadecimal")

    def test_home_only_lists_active_products_from_backend(self):
        LotteryProduct.objects.create(
            code=LotteryProduct.Code.OCTAL,
            name="Octal público activo",
            allowed_symbols="01234567",
            selection_count=4,
            is_active=True,
        )
        LotteryProduct.objects.create(
            code=LotteryProduct.Code.DECIMAL,
            name="Decimal público inactivo",
            allowed_symbols="0123456789",
            selection_count=5,
            is_active=False,
        )

        response = self.client.get(reverse("core:home"))

        self.assertContains(response, "Octal público activo")
        self.assertNotContains(response, "Decimal público inactivo")

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("core:client_dashboard"))
        expected = (
            f"{reverse('accounts:login')}?next="
            f"{reverse('core:client_dashboard')}"
        )
        self.assertRedirects(response, expected)

    def test_client_navigation_does_not_show_vendor_or_admin_actions(self):
        user = create_user(roles=(CLIENT, VENDOR, ADMINISTRATOR))
        self.activate(user, CLIENT)

        response = self.client.get(reverse("core:client_dashboard"))

        self.assertContains(response, "Panel Cliente")
        self.assertNotContains(response, "Panel Vendedor")
        self.assertNotContains(response, "Panel Administrador")

    def test_staff_user_in_client_mode_does_not_see_admin_navigation(self):
        user = create_user(
            roles=(CLIENT, ADMINISTRATOR),
            is_staff=True,
            is_superuser=True,
        )
        self.activate(user, CLIENT)

        response = self.client.get(reverse("core:client_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, f'href="{reverse("admin:index")}"')

    def test_client_dashboard_uses_real_wallet_and_movement_data(self):
        user = create_user(
            username="dashboard_client",
            email="dashboard.client@example.test",
            document="DASH-CLIENT-001",
            roles=(CLIENT,),
        )
        real_wallet = Wallet.objects.get(
            user=user,
            currency=Wallet.Currency.REAL,
        )
        virtual_wallet = Wallet.objects.get(
            user=user,
            currency=Wallet.Currency.VIRTUAL,
        )
        Wallet.objects.filter(pk=real_wallet.pk).update(
            available_minor=12345,
            reserved_minor=500,
        )
        Wallet.objects.filter(pk=virtual_wallet.pk).update(
            available_minor=250,
        )
        Movement.objects.create(
            wallet=virtual_wallet,
            type=Movement.Type.PRIZE,
            direction=Movement.Direction.CREDIT,
            amount_minor=250,
            balance_after_minor=250,
            description="Premio visible del dashboard",
        )
        self.activate(user, CLIENT)

        response = self.client.get(reverse("core:client_dashboard"))

        self.assertContains(response, "$ 123.45")
        self.assertContains(response, "$ 5.00")
        self.assertContains(response, "V 2.50")
        self.assertContains(response, "Premio")
        self.assertContains(response, reverse("finance:wallet_detail"))
        self.assertNotContains(response, "Comprar boleto")
        self.assertContains(response, "Operaciones REAL")
        self.assertContains(response, "Conversión de wallets")
        self.assertContains(response, "Transferir VIRTUAL")

        self.assertContains(
            response,
            reverse("finance:real_operations"),
        )
        self.assertContains(
            response,
            reverse("finance:wallet_conversion"),
        )
        self.assertContains(
            response,
            reverse("finance:virtual_transfer"),
        )
        self.assertNotContains(
            response,
            f'href="{reverse("finance:topup")}"',
        )
        self.assertNotContains(
            response,
            f'href="{reverse("finance:conversion")}"',
        )
        self.assertNotContains(
            response,
            f'href="{reverse("finance:withdrawal")}"',
        )

    def test_vendor_dashboard_has_no_ticket_purchase_action(self):
        user = create_user(roles=(VENDOR,))
        self.activate(user, VENDOR)

        response = self.client.get(reverse("core:vendor_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Comprar boleto")
        self.assertNotContains(response, "Ir a compra mayorista")

    def test_vendor_dashboard_uses_own_wallets_and_assignments(self):
        vendor_user = create_user(
            username="dashboard_vendor",
            email="dashboard.vendor@example.test",
            document="DASH-VENDOR-001",
            roles=(VENDOR,),
        )
        client_user = create_user(
            username="assigned_client",
            email="assigned.client@example.test",
            document="ASSIGNED-CLIENT-001",
            roles=(CLIENT,),
        )
        profile = VendorProfile.objects.create(
            user=vendor_user,
            status=VendorProfile.Status.ACTIVE,
        )
        conversion_request = ConversionRequest.objects.create(
            client=client_user,
            amount_minor=500,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        ConversionAssignment.objects.create(
            request=conversion_request,
            vendor=profile,
            status=ConversionAssignment.Status.ACTIVE,
        )
        Wallet.objects.filter(
            user=vendor_user,
            currency=Wallet.Currency.REAL,
        ).update(available_minor=9000)
        self.activate(vendor_user, VENDOR)

        response = self.client.get(reverse("core:vendor_dashboard"))

        self.assertContains(response, "$ 90.00")
        self.assertContains(response, "assigned_client")
        self.assertContains(response, "$ 5.00")
        self.assertEqual(response.context["pending_request_count"], 1)
        self.assertContains(response, reverse("finance:wallet_detail"))

    def test_non_staff_administrator_mode_does_not_expose_django_admin(self):
        user = create_user(roles=(ADMINISTRATOR,))
        self.activate(user, ADMINISTRATOR)

        response = self.client.get(reverse("core:admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Abrir administración Django")
        self.assertNotContains(response, f'href="{reverse("admin:index")}"')
        self.assertContains(response, reverse("core:audit_list"))

    def test_staff_administrator_mode_exposes_only_implemented_admin_modules(self):
        user = create_user(
            roles=(ADMINISTRATOR,),
            is_staff=True,
            is_superuser=True,
        )
        self.activate(user, ADMINISTRATOR)

        response = self.client.get(reverse("core:admin_dashboard"))

        self.assertContains(response, "Abrir administración Django")
        self.assertContains(response, "Usuarios")
        self.assertContains(response, "Versiones legales")
        self.assertContains(response, "Eventos de sorteo")
        self.assertContains(response, "Auditoría administrativa")
        self.assertNotContains(response, "Administrar eventos")

    def test_admin_dashboard_shows_recent_audit_data(self):
        user = create_user(
            username="dashboard_admin",
            email="dashboard.admin@example.test",
            document="DASH-ADMIN-001",
            roles=(ADMINISTRATOR,),
        )
        AuditEvent.objects.create(
            actor=user,
            active_mode=ADMINISTRATOR,
            action="DASHBOARD_AUDIT_VISIBLE",
            resource_type="finance.Wallet",
            resource_id="1",
            reason="Prueba de dashboard.",
        )
        self.activate(user, ADMINISTRATOR)

        response = self.client.get(reverse("core:admin_dashboard"))

        self.assertContains(response, "DASHBOARD_AUDIT_VISIBLE")
        self.assertEqual(response.context["audit_event_count"], 1)

    def test_selector_empty_state_when_account_has_no_roles(self):
        user = create_user(roles=())
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:choose_mode"))

        self.assertContains(response, "No tienes modos asignados")
        self.assertEqual(Group.objects.count(), 0)

    def test_non_staff_administrator_does_not_receive_aggregate_counts(self):
        user = create_user(roles=(ADMINISTRATOR,))
        create_user(
            username="segundo_usuario",
            email="segundo@example.test",
            document="TEST-002",
        )
        self.activate(user, ADMINISTRATOR)

        response = self.client.get(reverse("core:admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["admin_access_ready"])
        self.assertIsNone(response.context["active_user_count"])
        self.assertIsNone(response.context["active_vendor_count"])
        self.assertNotContains(response, "Usuarios activos")
        self.assertContains(response, "No se muestran métricas")


class AuditReadOnlyViewTests(TestCase):
    def activate(self, user, mode):
        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = mode
        session.save()

    def create_event(
        self,
        *,
        actor,
        action="AUDIT_TEST_ACTION",
        resource_type="finance.Wallet",
        resource_id="1",
        active_mode=ADMINISTRATOR,
    ):
        return AuditEvent.objects.create(
            actor=actor,
            active_mode=active_mode,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            reason="Motivo académico controlado.",
            metadata="resultado=permitido",
            ip_address="127.0.0.1",
        )

    def test_anonymous_user_is_redirected_to_login(self):
        url = reverse("core:audit_list")

        response = self.client.get(url)

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={url}",
        )

    def test_client_and_vendor_modes_receive_403(self):
        for index, mode in enumerate((CLIENT, VENDOR), start=1):
            user = create_user(
                username=f"audit_denied_{index}",
                email=f"audit.denied.{index}@example.test",
                document=f"AUDIT-DENIED-{index}",
                roles=(mode,),
            )
            self.activate(user, mode)

            with self.subTest(mode=mode):
                response = self.client.get(reverse("core:audit_list"))
                self.assertEqual(response.status_code, 403)

            self.client.logout()

    def test_administrator_requires_administrator_active_mode(self):
        user = create_user(roles=(CLIENT, ADMINISTRATOR))
        self.activate(user, CLIENT)

        response = self.client.get(reverse("core:audit_list"))

        self.assertEqual(response.status_code, 403)

    def test_non_staff_administrator_can_open_audit_list(self):
        user = create_user(roles=(ADMINISTRATOR,))
        self.create_event(actor=user)
        self.activate(user, ADMINISTRATOR)

        response = self.client.get(reverse("core:audit_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/audit_list.html")
        self.assertContains(response, "AUDIT_TEST_ACTION")

    def test_audit_list_filters_by_action_resource_and_mode(self):
        user = create_user(roles=(ADMINISTRATOR,))
        self.create_event(
            actor=user,
            action="KEEP_ACTION",
            resource_type="finance.Wallet",
        )
        self.create_event(
            actor=user,
            action="HIDE_ACTION",
            resource_type="lottery.Ticket",
        )
        self.activate(user, ADMINISTRATOR)

        response = self.client.get(
            reverse("core:audit_list"),
            {
                "action": "KEEP_ACTION",
                "resource_type": "finance.Wallet",
                "mode": ADMINISTRATOR,
            },
        )

        page_obj = response.context["page_obj"]
        visible_events = list(page_obj.object_list)

        self.assertEqual(len(visible_events), 1)
        self.assertEqual(visible_events[0].action, "KEEP_ACTION")
        self.assertEqual(
            visible_events[0].resource_type,
            "finance.Wallet",
        )
        self.assertEqual(
            visible_events[0].active_mode,
            "ADMINISTRADOR",
        )
        
    def test_audit_list_is_paginated(self):
        user = create_user(roles=(ADMINISTRATOR,))
        for index in range(21):
            self.create_event(
                actor=user,
                action=f"AUDIT_PAGE_{index:02d}",
                resource_id=str(index),
            )
        self.activate(user, ADMINISTRATOR)

        first_page = self.client.get(reverse("core:audit_list"))
        second_page = self.client.get(
            reverse("core:audit_list"),
            {"page": 2},
        )

        self.assertEqual(len(first_page.context["audit_events"]), 20)
        self.assertEqual(len(second_page.context["audit_events"]), 1)
        self.assertTrue(first_page.context["is_paginated"])

    def test_audit_detail_is_read_only_and_requires_admin_mode(self):
        administrator = create_user(
            username="audit_detail_admin",
            email="audit.detail.admin@example.test",
            document="AUDIT-DETAIL-ADMIN",
            roles=(ADMINISTRATOR,),
        )
        client = create_user(
            username="audit_detail_client",
            email="audit.detail.client@example.test",
            document="AUDIT-DETAIL-CLIENT",
            roles=(CLIENT,),
        )
        event = self.create_event(
            actor=administrator,
            action="AUDIT_DETAIL_VISIBLE",
        )

        self.activate(administrator, ADMINISTRATOR)
        allowed = self.client.get(
            reverse("core:audit_detail", kwargs={"pk": event.pk})
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertContains(allowed, "AUDIT_DETAIL_VISIBLE")
        self.assertNotContains(allowed, "Editar")
        self.client.logout()

        self.activate(client, CLIENT)
        denied = self.client.get(
            reverse("core:audit_detail", kwargs={"pk": event.pk})
        )
        self.assertEqual(denied.status_code, 403)

    def test_missing_audit_detail_returns_404_for_administrator(self):
        user = create_user(roles=(ADMINISTRATOR,))
        self.activate(user, ADMINISTRATOR)

        response = self.client.get(
            reverse("core:audit_detail", kwargs={"pk": 999999})
        )

        self.assertEqual(response.status_code, 404)

    def test_audit_list_and_detail_reject_post(self):
        user = create_user(roles=(ADMINISTRATOR,))
        event = self.create_event(actor=user)
        self.activate(user, ADMINISTRATOR)

        list_response = self.client.post(reverse("core:audit_list"), {})
        detail_response = self.client.post(
            reverse("core:audit_detail", kwargs={"pk": event.pk}),
            {},
        )

        self.assertEqual(list_response.status_code, 405)
        self.assertEqual(detail_response.status_code, 405)
