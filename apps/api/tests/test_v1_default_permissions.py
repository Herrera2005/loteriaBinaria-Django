from __future__ import annotations

from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings


class ApiV1DefaultPermissionTests(SimpleTestCase):
    def test_default_permission_is_authenticated(self):
        self.assertEqual(
            api_settings.DEFAULT_PERMISSION_CLASSES,
            [
                IsAuthenticated,
            ],
        )


class ApiV1PublicAccessRegressionTests(TestCase):
    def test_health_remains_public(self):
        response = self.client.get(
            reverse("api:v1-health")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_public_products_remain_public(self):
        response = self.client.get(
            reverse(
                "api:v1-public-product-list"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_public_events_remain_public(self):
        response = self.client.get(
            reverse(
                "api:v1-public-event-list"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_public_results_remain_public(self):
        response = self.client.get(
            reverse(
                "api:v1-public-result-list"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )