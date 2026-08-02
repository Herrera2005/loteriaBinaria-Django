from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.policies import (
    can_purchase_ticket,
    can_use_administrator_functions,
    can_use_client_functions,
    can_use_vendor_functions,
)
from apps.accounts.roles import ADMINISTRATOR, CLIENT, VENDOR

from .factories import VALID_PASSWORD, create_user


class PermissionMatrixTests(TestCase):
    def _set_mode(self, mode):
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = mode
        session.save()

    def test_single_client_role_enters_directly(self):
        create_user(roles=(CLIENT,))

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "usuario_prueba",
                "password": VALID_PASSWORD,
            },
        )

        self.assertRedirects(response, reverse("core:client_dashboard"))
        self.assertEqual(
            self.client.session[ACTIVE_MODE_SESSION_KEY],
            CLIENT,
        )

    def test_multirole_login_requires_selector(self):
        create_user(roles=(CLIENT, VENDOR))

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "usuario_prueba",
                "password": VALID_PASSWORD,
            },
        )

        self.assertRedirects(response, reverse("accounts:choose_mode"))
        self.assertNotIn(ACTIVE_MODE_SESSION_KEY, self.client.session)

    def test_change_mode_accepts_only_assigned_groups(self):
        user = create_user(roles=(CLIENT, VENDOR))
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:choose_mode"),
            {"mode": ADMINISTRATOR},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(ACTIVE_MODE_SESSION_KEY, self.client.session)

    def test_change_mode_post_requires_csrf(self):
        user = create_user(roles=(CLIENT, VENDOR))
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(user)

        response = csrf_client.post(
            reverse("accounts:choose_mode"),
            {"mode": CLIENT},
        )

        self.assertEqual(response.status_code, 403)

    def test_multirole_client_mode_keeps_client_permissions(self):
        user = create_user(
            roles=(CLIENT, VENDOR, ADMINISTRATOR),
            is_staff=True,
        )
        self.client.force_login(user)
        self._set_mode(CLIENT)

        response = self.client.get(reverse("core:client_dashboard"))

        self.assertEqual(response.status_code, 200)
        request = response.wsgi_request
        self.assertTrue(can_use_client_functions(request))
        self.assertTrue(can_purchase_ticket(request))
        self.assertFalse(can_use_vendor_functions(request))
        self.assertFalse(can_use_administrator_functions(request))

    def test_vendor_and_administrator_modes_cannot_purchase(self):
        user = create_user(
            roles=(CLIENT, VENDOR, ADMINISTRATOR),
            is_staff=True,
        )
        self.client.force_login(user)

        for mode, dashboard_name in (
            (VENDOR, "core:vendor_dashboard"),
            (ADMINISTRATOR, "core:admin_dashboard"),
        ):
            with self.subTest(mode=mode):
                self._set_mode(mode)
                response = self.client.get(reverse(dashboard_name))
                self.assertEqual(response.status_code, 200)
                self.assertFalse(
                    can_purchase_ticket(response.wsgi_request)
                )

    def test_navigation_comes_from_active_mode(self):
        user = create_user(roles=(CLIENT, VENDOR))
        self.client.force_login(user)
        self._set_mode(CLIENT)

        response = self.client.get(reverse("core:client_dashboard"))

        labels = [item["label"] for item in response.context["nav_items"]]
        self.assertIn("Panel Cliente", labels)
        self.assertNotIn("Panel Vendedor", labels)
        self.assertNotIn("Panel Administrador", labels)
