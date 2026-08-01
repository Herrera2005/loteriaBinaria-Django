from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import ADMINISTRATOR, CLIENT, VENDOR
from apps.accounts.tests.factories import create_user


class PublicAndDashboardViewTests(TestCase):
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

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("core:client_dashboard"))
        expected = f"{reverse('accounts:login')}?next={reverse('core:client_dashboard')}"
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

    def test_vendor_dashboard_has_no_ticket_purchase_action(self):
        user = create_user(roles=(VENDOR,))
        self.activate(user, VENDOR)

        response = self.client.get(reverse("core:vendor_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Comprar boleto")
        self.assertNotContains(response, "Ir a compra mayorista")

    def test_non_staff_administrator_mode_does_not_expose_django_admin(self):
        user = create_user(roles=(ADMINISTRATOR,))
        self.activate(user, ADMINISTRATOR)

        response = self.client.get(reverse("core:admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Abrir administración Django")
        self.assertNotContains(response, f'href="{reverse("admin:index")}"')

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
        self.assertNotContains(response, "Administrar eventos")

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
        self.assertContains(response, "No se muestran conteos")

