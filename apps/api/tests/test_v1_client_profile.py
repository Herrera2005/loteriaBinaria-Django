from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from apps.accounts.roles import (
    CLIENT,
    VENDOR,
)


User = get_user_model()


class ApiV1ClientProfileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_group = Group.objects.create(
            name=CLIENT,
        )

        cls.vendor_group = Group.objects.create(
            name=VENDOR,
        )

        cls.client_user = User.objects.create_user(
            username="client_profile",
            email="client.profile@example.com",
            password="ClientProfile123!",
            first_name="Cliente",
            last_name="Profile",
            document="API-CLIENT-PROFILE-001",
            birth_date=date(2000, 1, 1),
        )

        cls.client_user.groups.add(
            cls.client_group,
        )

        cls.multirole_user = User.objects.create_user(
            username="client_multi",
            email="client.multi@example.com",
            password="ClientProfile123!",
            first_name="Cliente",
            last_name="Multi",
            document="API-CLIENT-PROFILE-002",
            birth_date=date(2000, 1, 1),
        )

        cls.multirole_user.groups.add(
            cls.client_group,
            cls.vendor_group,
        )

        cls.vendor_only_user = User.objects.create_user(
            username="vendor_only",
            email="vendor.only@example.com",
            password="ClientProfile123!",
            first_name="Vendor",
            last_name="Only",
            document="API-VENDOR-ONLY-001",
            birth_date=date(2000, 1, 1),
        )

        cls.vendor_only_user.groups.add(
            cls.vendor_group,
        )

    @staticmethod
    def _token_for(user):
        return Token.objects.create(
            user=user,
        )

    def test_client_profile_requires_authentication(self):
        response = self.client.get(
            reverse("api:v1-client-profile"),
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_client_profile_requires_active_mode_header(self):
        token = self._token_for(
            self.client_user,
        )

        response = self.client.get(
            reverse("api:v1-client-profile"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_client_profile_accepts_client_mode(self):
        token = self._token_for(
            self.client_user,
        )

        response = self.client.get(
            reverse("api:v1-client-profile"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["active_mode"],
            CLIENT,
        )

        self.assertEqual(
            payload["user"]["id"],
            self.client_user.pk,
        )

        self.assertEqual(
            payload["user"]["roles"],
            [CLIENT],
        )

    def test_multirole_user_can_enter_client_mode(self):
        token = self._token_for(
            self.multirole_user,
        )

        response = self.client.get(
            reverse("api:v1-client-profile"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["active_mode"],
            CLIENT,
        )

    def test_multirole_user_cannot_use_vendor_mode_on_client_endpoint(self):
        token = self._token_for(
            self.multirole_user,
        )

        response = self.client.get(
            reverse("api:v1-client-profile"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
            HTTP_X_ACTIVE_MODE=VENDOR,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_vendor_only_user_cannot_enter_client_endpoint(self):
        token = self._token_for(
            self.vendor_only_user,
        )

        response = self.client.get(
            reverse("api:v1-client-profile"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_client_profile_does_not_expose_sensitive_fields(self):
        token = self._token_for(
            self.client_user,
        )

        response = self.client.get(
            reverse("api:v1-client-profile"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        user = response.json()["user"]

        self.assertNotIn(
            "password",
            user,
        )
        self.assertNotIn(
            "document",
            user,
        )
        self.assertNotIn(
            "birth_date",
            user,
        )
        self.assertNotIn(
            "is_staff",
            user,
        )
        self.assertNotIn(
            "is_superuser",
            user,
        )