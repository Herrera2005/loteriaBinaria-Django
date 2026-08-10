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


class ApiV1AuthTests(TestCase):
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

        cls.noncanonical_group = Group.objects.create(
            name="GRUPO_INTERNO_PRUEBA",
        )

        cls.password = "ApiTestPassword123!"

        cls.user = User.objects.create_user(
            username="cliente_api",
            email="cliente.api@example.com",
            password=cls.password,
            first_name="Cliente",
            last_name="API",
            document="API-CLIENTE-001",
            birth_date=date(2000, 1, 1),
        )

        cls.user.groups.add(
            cls.client_group,
        )

        cls.multirole_user = User.objects.create_user(
            username="multi_api",
            email="multi.api@example.com",
            password=cls.password,
            first_name="Multi",
            last_name="Rol",
            document="API-MULTI-001",
            birth_date=date(2000, 1, 1),
        )

        cls.multirole_user.groups.add(
            cls.client_group,
            cls.vendor_group,
        )

        cls.user_with_extra_group = User.objects.create_user(
            username="extra_api",
            email="extra.api@example.com",
            password=cls.password,
            first_name="Extra",
            last_name="Group",
            document="API-EXTRA-001",
            birth_date=date(2000, 1, 1),
        )

        cls.user_with_extra_group.groups.add(
            cls.client_group,
            cls.noncanonical_group,
        )

        cls.suspended_user = User.objects.create_user(
            username="suspendido_api",
            email="suspendido.api@example.com",
            password=cls.password,
            first_name="Suspendido",
            last_name="API",
            document="API-SUSP-001",
            birth_date=date(2000, 1, 1),
        )

        cls.suspended_user.status = User.Status.SUSPENDED
        cls.suspended_user.is_active = False
        cls.suspended_user.save(
            update_fields=[
                "status",
                "is_active",
            ]
        )

        cls.blocked_user = User.objects.create_user(
            username="bloqueado_api",
            email="bloqueado.api@example.com",
            password=cls.password,
            first_name="Bloqueado",
            last_name="API",
            document="API-BLOCK-001",
            birth_date=date(2000, 1, 1),
        )

        cls.blocked_user.status = User.Status.BLOCKED
        cls.blocked_user.is_active = False
        cls.blocked_user.save(
            update_fields=[
                "status",
                "is_active",
            ]
        )

    def test_login_accepts_username(self):
        response = self.client.post(
            reverse("api:v1-auth-login"),
            data={
                "identifier": self.user.username,
                "password": self.password,
            },
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertIn(
            "token",
            payload,
        )

        self.assertEqual(
            payload["user"]["username"],
            self.user.username,
        )

        self.assertEqual(
            payload["user"]["roles"],
            [CLIENT],
        )

    def test_login_accepts_email_case_insensitively(self):
        response = self.client.post(
            reverse("api:v1-auth-login"),
            data={
                "identifier": "CLIENTE.API@EXAMPLE.COM",
                "password": self.password,
            },
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["user"]["id"],
            self.user.pk,
        )

    def test_login_accepts_username_case_insensitively(self):
        response = self.client.post(
            reverse("api:v1-auth-login"),
            data={
                "identifier": "CLIENTE_API",
                "password": self.password,
            },
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_invalid_password_does_not_authenticate(self):
        response = self.client.post(
            reverse("api:v1-auth-login"),
            data={
                "identifier": self.user.username,
                "password": "incorrecta",
            },
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            Token.objects.filter(
                user=self.user,
            ).exists()
        )

    def test_unknown_user_does_not_authenticate(self):
        response = self.client.post(
            reverse("api:v1-auth-login"),
            data={
                "identifier": "no-existe",
                "password": self.password,
            },
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_login_returns_all_assigned_roles_in_canonical_order(self):
        response = self.client.post(
            reverse("api:v1-auth-login"),
            data={
                "identifier": self.multirole_user.username,
                "password": self.password,
            },
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["user"]["roles"],
            [
                CLIENT,
                VENDOR,
            ],
        )

    def test_noncanonical_groups_are_not_exposed_as_roles(self):
        response = self.client.post(
            reverse("api:v1-auth-login"),
            data={
                "identifier": self.user_with_extra_group.username,
                "password": self.password,
            },
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["user"]["roles"],
            [
                CLIENT,
            ],
        )

    def test_suspended_user_cannot_log_in(self):
        response = self.client.post(
            reverse("api:v1-auth-login"),
            data={
                "identifier": self.suspended_user.username,
                "password": self.password,
            },
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            Token.objects.filter(
                user=self.suspended_user,
            ).exists()
        )

        payload = response.json()

        self.assertEqual(
            payload["error"]["code"],
            "BAD_REQUEST",
        )

        self.assertIn(
            "identifier",
            payload["error"]["fields"],
        )

    def test_blocked_user_cannot_log_in(self):
        response = self.client.post(
            reverse("api:v1-auth-login"),
            data={
                "identifier": self.blocked_user.username,
                "password": self.password,
            },
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertFalse(
            Token.objects.filter(
                user=self.blocked_user,
            ).exists()
        )

    def test_me_requires_authentication(self):
        response = self.client.get(
            reverse("api:v1-auth-me")
        )

        self.assertEqual(
            response.status_code,
            401,
        )

        payload = response.json()

        self.assertEqual(
            payload["error"]["code"],
            "AUTHENTICATION_REQUIRED",
        )

    def test_me_returns_authenticated_user(self):
        token = Token.objects.create(
            user=self.user,
        )

        response = self.client.get(
            reverse("api:v1-auth-me"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["user"]["id"],
            self.user.pk,
        )

        self.assertEqual(
            payload["user"]["roles"],
            [CLIENT],
        )

    def test_me_does_not_expose_sensitive_user_fields(self):
        token = Token.objects.create(
            user=self.user,
        )

        response = self.client.get(
            reverse("api:v1-auth-me"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        user_payload = response.json()["user"]

        self.assertEqual(
            set(user_payload.keys()),
            {
                "id",
                "username",
                "email",
                "first_name",
                "last_name",
                "roles",
            },
        )

        self.assertNotIn(
            "password",
            user_payload,
        )

        self.assertNotIn(
            "document",
            user_payload,
        )

        self.assertNotIn(
            "birth_date",
            user_payload,
        )

        self.assertNotIn(
            "is_superuser",
            user_payload,
        )

        self.assertNotIn(
            "is_staff",
            user_payload,
        )

    def test_invalid_token_is_rejected(self):
        response = self.client.get(
            reverse("api:v1-auth-me"),
            HTTP_AUTHORIZATION="Token token-invalido",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_logout_requires_authentication(self):
        response = self.client.post(
            reverse("api:v1-auth-logout"),
            data={},
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_logout_deletes_current_token(self):
        token = Token.objects.create(
            user=self.user,
        )

        response = self.client.post(
            reverse("api:v1-auth-logout"),
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

        self.assertEqual(
            response.status_code,
            204,
        )

        self.assertFalse(
            Token.objects.filter(
                key=token.key,
            ).exists()
        )

    def test_logged_out_token_cannot_be_reused(self):
        token = Token.objects.create(
            user=self.user,
        )

        self.client.post(
            reverse("api:v1-auth-logout"),
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

        response = self.client.get(
            reverse("api:v1-auth-me"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

        self.assertEqual(
            response.status_code,
            401,
        )