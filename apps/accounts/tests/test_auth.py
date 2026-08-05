from __future__ import annotations

from django.contrib.auth import SESSION_KEY
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.roles import CLIENT, VENDOR

from .factories import VALID_PASSWORD, create_user


class RealAuthenticationTests(TestCase):
    def test_login_accepts_username(self):
        create_user(username="cliente_login", roles=(CLIENT,))

        response = self.client.post(
            reverse("accounts:login"),
            {"username": " CLIENTE_LOGIN ", "password": VALID_PASSWORD},
        )

        self.assertRedirects(response, reverse("core:client_dashboard"))
        self.assertIn(SESSION_KEY, self.client.session)

    def test_login_accepts_email_case_insensitively(self):
        user = create_user(
            username="cliente_email",
            email="cliente.email@example.test",
            document="AUTH-EMAIL-001",
            roles=(CLIENT,),
        )

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": " CLIENTE.EMAIL@EXAMPLE.TEST ",
                "password": VALID_PASSWORD,
            },
        )

        self.assertRedirects(response, reverse("core:client_dashboard"))
        self.assertEqual(int(self.client.session[SESSION_KEY]), user.pk)

    def test_invalid_credentials_do_not_authenticate(self):
        create_user(username="cliente_invalido", roles=(CLIENT,))

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "cliente_invalido", "password": "incorrecta"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No fue posible iniciar sesión")
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_external_next_is_rejected(self):
        create_user(username="cliente_next", roles=(CLIENT,))

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "cliente_next",
                "password": VALID_PASSWORD,
                "next": "https://evil.example/phishing",
            },
        )

        self.assertRedirects(response, reverse("core:client_dashboard"))

    def test_internal_next_is_used_for_single_role(self):
        create_user(username="cliente_safe_next", roles=(CLIENT,))
        destination = reverse("accounts:profile")

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "cliente_safe_next",
                "password": VALID_PASSWORD,
                "next": destination,
            },
        )

        self.assertRedirects(response, destination)

    def test_multirole_safe_next_is_applied_after_mode_selection(self):
        user = create_user(
            username="multirole_next",
            document="AUTH-MULTI-001",
            roles=(CLIENT, VENDOR),
        )
        destination = reverse("accounts:profile")

        login_response = self.client.post(
            reverse("accounts:login"),
            {
                "username": user.username,
                "password": VALID_PASSWORD,
                "next": destination,
            },
        )
        self.assertRedirects(login_response, reverse("accounts:choose_mode"))

        mode_response = self.client.post(
            reverse("accounts:choose_mode"),
            {"mode": CLIENT},
        )
        self.assertRedirects(mode_response, destination)

    def test_logout_is_post_only_and_clears_session(self):
        user = create_user(username="logout_real", roles=(CLIENT,))
        self.client.force_login(user)

        self.assertEqual(
            self.client.get(reverse("accounts:logout")).status_code,
            405,
        )
        response = self.client.post(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("core:home"))
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_logout_post_requires_csrf(self):
        user = create_user(username="logout_csrf", roles=(CLIENT,))
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(user)

        response = csrf_client.post(reverse("accounts:logout"))

        self.assertEqual(response.status_code, 403)
        self.assertIn(SESSION_KEY, csrf_client.session)


class PasswordChangeTests(TestCase):
    def setUp(self):
        self.user = create_user(
            username="password_owner",
            document="AUTH-PASSWORD-001",
            roles=(CLIENT,),
        )
        self.client.force_login(self.user)
        self.url = reverse("accounts:password_change")

    def test_anonymous_user_is_redirected_to_login(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={self.url}",
        )

    def test_password_change_rejects_wrong_current_password(self):
        response = self.client.post(
            self.url,
            {
                "old_password": "incorrecta",
                "new_password1": "NuevaClaveSegura9!",
                "new_password2": "NuevaClaveSegura9!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "contraseña antigua")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(VALID_PASSWORD))

    def test_password_change_updates_hash_and_keeps_session(self):
        new_password = "NuevaClaveSegura9!"

        response = self.client.post(
            self.url,
            {
                "old_password": VALID_PASSWORD,
                "new_password1": new_password,
                "new_password2": new_password,
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:password_change_done"),
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.assertIn(SESSION_KEY, self.client.session)

    def test_password_change_post_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        response = csrf_client.post(
            self.url,
            {
                "old_password": VALID_PASSWORD,
                "new_password1": "NuevaClaveSegura9!",
                "new_password2": "NuevaClaveSegura9!",
            },
        )

        self.assertEqual(response.status_code, 403)
