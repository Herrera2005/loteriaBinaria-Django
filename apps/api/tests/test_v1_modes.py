from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from apps.accounts.roles import (
    ADMINISTRATOR,
    CLIENT,
    VENDOR,
)


User = get_user_model()


class ApiV1ModeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_group = Group.objects.create(
            name=CLIENT,
        )

        cls.vendor_group = Group.objects.create(
            name=VENDOR,
        )

        cls.admin_group = Group.objects.create(
            name=ADMINISTRATOR,
        )

        cls.password = "ApiModePassword123!"

        cls.multirole_user = User.objects.create_user(
            username="mode_multi",
            email="mode.multi@example.com",
            password=cls.password,
            first_name="Mode",
            last_name="Multi",
            document="API-MODE-001",
            birth_date=date(2000, 1, 1),
        )

        cls.multirole_user.groups.add(
            cls.client_group,
            cls.vendor_group,
        )

        cls.client_user = User.objects.create_user(
            username="mode_client",
            email="mode.client@example.com",
            password=cls.password,
            first_name="Mode",
            last_name="Client",
            document="API-MODE-002",
            birth_date=date(2000, 1, 1),
        )

        cls.client_user.groups.add(
            cls.client_group,
        )

    def _token_for(self, user):
        return Token.objects.create(
            user=user
        )

    def test_mode_endpoint_requires_authentication(self):
        response = self.client.get(
            reverse("api:v1-auth-mode")
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_mode_endpoint_returns_available_modes(self):
        token = self._token_for(
            self.multirole_user
        )

        response = self.client.get(
            reverse("api:v1-auth-mode"),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertIsNone(
            payload["requested_mode"]
        )

        self.assertIsNone(
            payload["active_mode"]
        )

        self.assertEqual(
            payload["available_modes"],
            [
                CLIENT,
                VENDOR,
            ],
        )

    def test_mode_header_is_case_insensitive_in_value(self):
        token = self._token_for(
            self.multirole_user
        )

        response = self.client.get(
            reverse("api:v1-auth-mode"),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE="cliente",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["requested_mode"],
            CLIENT,
        )

        self.assertEqual(
            payload["active_mode"],
            CLIENT,
        )

    def test_mode_endpoint_does_not_accept_unassigned_role(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse("api:v1-auth-mode"),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=VENDOR,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["requested_mode"],
            VENDOR,
        )

        self.assertIsNone(
            payload["active_mode"]
        )

        self.assertEqual(
            payload["available_modes"],
            [
                CLIENT,
            ],
        )

    def test_context_requires_active_mode_header(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse("api:v1-auth-context"),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            response.json()["error"]["code"],
            "PERMISSION_DENIED",
        )

    def test_context_accepts_assigned_mode(self):
        token = self._token_for(
            self.multirole_user
        )

        response = self.client.get(
            reverse("api:v1-auth-context"),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=VENDOR,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["active_mode"],
            VENDOR,
        )

        self.assertEqual(
            payload["user"]["id"],
            self.multirole_user.pk,
        )

    def test_context_rejects_unassigned_mode(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse("api:v1-auth-context"),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=VENDOR,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            response.json()["error"]["code"],
            "PERMISSION_DENIED",
        )

    def test_context_rejects_unknown_mode(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse("api:v1-auth-context"),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE="NO_EXISTE",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_context_does_not_trust_admin_header(self):
        token = self._token_for(
            self.client_user
        )

        response = self.client.get(
            reverse("api:v1-auth-context"),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=ADMINISTRATOR,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_context_rejects_user_suspended_after_token_creation(self):
        token = self._token_for(
            self.client_user
        )

        self.client_user.status = (
            User.Status.SUSPENDED
        )
        self.client_user.is_active = False
        self.client_user.save(
            update_fields=[
                "status",
                "is_active",
            ]
        )

        response = self.client.get(
            reverse("api:v1-auth-context"),
            HTTP_AUTHORIZATION=(
                f"Token {token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertIn(
            response.status_code,
            {
                401,
                403,
            },
        )