from django.test import TestCase
from django.urls import reverse

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.models import User
from apps.accounts.roles import ADMINISTRATOR, CLIENT, VENDOR

from .factories import VALID_PASSWORD, create_user


class AuthenticationAndModeTests(TestCase):
    def test_single_role_login_selects_mode_and_redirects_to_dashboard(self):
        create_user(roles=(CLIENT,))

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "usuario_prueba", "password": VALID_PASSWORD},
        )

        self.assertRedirects(response, reverse("core:client_dashboard"))
        self.assertEqual(
            self.client.session[ACTIVE_MODE_SESSION_KEY],
            CLIENT,
        )

    def test_multirole_login_requires_explicit_mode_selection(self):
        create_user(roles=(CLIENT, VENDOR))

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "usuario_prueba", "password": VALID_PASSWORD},
        )

        self.assertRedirects(response, reverse("accounts:choose_mode"))
        self.assertNotIn(ACTIVE_MODE_SESSION_KEY, self.client.session)

    def test_selector_only_accepts_assigned_roles(self):
        user = create_user(roles=(CLIENT, VENDOR))
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:choose_mode"),
            {"mode": ADMINISTRATOR},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seleccione una opción válida")
        self.assertNotIn(ACTIVE_MODE_SESSION_KEY, self.client.session)

    def test_mode_change_is_post_and_redirects_to_matching_dashboard(self):
        user = create_user(roles=(CLIENT, VENDOR))
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:choose_mode"),
            {"mode": VENDOR},
        )

        self.assertRedirects(response, reverse("core:vendor_dashboard"))
        self.assertEqual(self.client.session[ACTIVE_MODE_SESSION_KEY], VENDOR)

    def test_wrong_dashboard_for_active_mode_returns_403(self):
        user = create_user(roles=(CLIENT, VENDOR))
        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = CLIENT
        session.save()

        self.assertEqual(
            self.client.get(reverse("core:client_dashboard")).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("core:vendor_dashboard")).status_code,
            403,
        )

    def test_unassigned_mode_in_session_is_removed(self):
        user = create_user(roles=(CLIENT,))
        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = VENDOR
        session.save()

        response = self.client.get(reverse("core:client_dashboard"))

        self.assertRedirects(response, reverse("accounts:choose_mode"))
        self.assertNotIn(ACTIVE_MODE_SESSION_KEY, self.client.session)

    def test_suspended_business_status_cannot_log_in(self):
        user = create_user()
        User.objects.filter(pk=user.pk).update(
            status=User.Status.SUSPENDED,
            is_active=True,
        )

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "usuario_prueba", "password": VALID_PASSWORD},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cuenta no está activa")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_suspended_authenticated_user_cannot_select_mode(self):
        user = create_user(roles=(CLIENT,))
        self.client.force_login(user)
        User.objects.filter(pk=user.pk).update(
            status=User.Status.SUSPENDED,
            is_active=True,
        )

        response = self.client.get(reverse("accounts:choose_mode"))

        self.assertEqual(response.status_code, 403)

    def test_logout_rejects_get_and_accepts_post(self):
        user = create_user(roles=(CLIENT,))
        self.client.force_login(user)

        self.assertEqual(
            self.client.get(reverse("accounts:logout")).status_code,
            405,
        )
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("core:home"))

    def test_login_normalizes_username_case_and_spaces(self):
        create_user(username="usuario_mixto", roles=(CLIENT,))

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "  USUARIO_MIXTO  ", "password": VALID_PASSWORD},
        )

        self.assertRedirects(response, reverse("core:client_dashboard"))
        self.assertIn("_auth_user_id", self.client.session)

