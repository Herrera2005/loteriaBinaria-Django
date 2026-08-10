from __future__ import annotations

from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from apps.accounts.roles import (
    CLIENT,
    VENDOR,
)
from apps.accounts.tests.factories import create_user
from apps.vendors.models import VendorProfile


class ApiV1VendorProfileTests(TestCase):
    def setUp(self):
        self.vendor_user = create_user(
            username="api_vendor_profile",
            email="api.vendor.profile@example.test",
            document="API-VENDOR-PROFILE",
            roles=(VENDOR,),
        )

        self.vendor_profile = (
            VendorProfile.objects.create(
                user=self.vendor_user,
                status=VendorProfile.Status.ACTIVE,
            )
        )

        self.vendor_token = Token.objects.create(
            user=self.vendor_user,
        )

        self.multirole_user = create_user(
            username="api_vendor_multi",
            email="api.vendor.multi@example.test",
            document="API-VENDOR-MULTI",
            roles=(
                CLIENT,
                VENDOR,
            ),
        )

        self.multirole_profile = (
            VendorProfile.objects.create(
                user=self.multirole_user,
                status=VendorProfile.Status.ACTIVE,
            )
        )

        self.multirole_token = Token.objects.create(
            user=self.multirole_user,
        )

        self.vendor_without_profile = create_user(
            username="api_vendor_no_profile",
            email="api.vendor.no.profile@example.test",
            document="API-VENDOR-NO-PROFILE",
            roles=(VENDOR,),
        )

        self.no_profile_token = Token.objects.create(
            user=self.vendor_without_profile,
        )

        self.client_only = create_user(
            username="api_client_only_vendor_test",
            email="api.client.only.vendor@example.test",
            document="API-CLIENT-ONLY-VENDOR",
            roles=(CLIENT,),
        )

        self.client_token = Token.objects.create(
            user=self.client_only,
        )

        self.url = reverse(
            "api:v1-vendor-profile"
        )

    def test_vendor_profile_requires_authentication(self):
        response = self.client.get(
            self.url
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_vendor_profile_requires_active_mode_header(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=(
                f"Token {self.vendor_token.key}"
            ),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_vendor_profile_requires_vendor_mode(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=(
                f"Token {self.multirole_token.key}"
            ),
            HTTP_X_ACTIVE_MODE=CLIENT,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_client_only_user_cannot_fake_vendor_mode(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=(
                f"Token {self.client_token.key}"
            ),
            HTTP_X_ACTIVE_MODE=VENDOR,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_vendor_role_without_profile_is_rejected(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=(
                f"Token {self.no_profile_token.key}"
            ),
            HTTP_X_ACTIVE_MODE=VENDOR,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_suspended_vendor_profile_is_rejected(self):
        self.vendor_profile.status = (
            VendorProfile.Status.SUSPENDED
        )

        self.vendor_profile.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=(
                f"Token {self.vendor_token.key}"
            ),
            HTTP_X_ACTIVE_MODE=VENDOR,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_active_vendor_can_access_profile(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=(
                f"Token {self.vendor_token.key}"
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
            self.vendor_user.pk,
        )

        self.assertEqual(
            payload["vendor_profile"]["id"],
            self.vendor_profile.pk,
        )

        self.assertEqual(
            payload["vendor_profile"]["status"],
            VendorProfile.Status.ACTIVE,
        )

        self.assertEqual(
            payload["vendor_profile"]["status_label"],
            "Activo",
        )

    def test_multirole_user_can_operate_as_vendor(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=(
                f"Token {self.multirole_token.key}"
            ),
            HTTP_X_ACTIVE_MODE=VENDOR,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["active_mode"],
            VENDOR,
        )

    def test_vendor_profile_contract_does_not_expose_sensitive_fields(self):
        response = self.client.get(
            self.url,
            HTTP_AUTHORIZATION=(
                f"Token {self.vendor_token.key}"
            ),
            HTTP_X_ACTIVE_MODE=VENDOR,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        profile = response.json()[
            "vendor_profile"
        ]

        self.assertEqual(
            set(profile.keys()),
            {
                "id",
                "status",
                "status_label",
                "activated_at",
                "created_at",
                "updated_at",
            },
        )

        self.assertNotIn(
            "user",
            profile,
        )

        self.assertNotIn(
            "user_id",
            profile,
        )