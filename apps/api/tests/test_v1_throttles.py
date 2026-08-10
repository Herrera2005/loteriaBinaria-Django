from __future__ import annotations

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from apps.api.v1.throttles import (
    UnsafeMethodScopedRateThrottle,
)
from django.urls import resolve, reverse

class DummyView:
    throttle_scope = "test_write"


class ApiV1ThrottleTests(
    SimpleTestCase
):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.throttle = (
            UnsafeMethodScopedRateThrottle()
        )
        self.view = DummyView()

    def test_get_bypasses_write_throttle(self):
        request = self.factory.get(
            "/api/v1/test/"
        )

        allowed = self.throttle.allow_request(
            request,
            self.view,
        )

        self.assertTrue(allowed)

    def test_head_bypasses_write_throttle(self):
        request = self.factory.head(
            "/api/v1/test/"
        )

        allowed = self.throttle.allow_request(
            request,
            self.view,
        )

        self.assertTrue(allowed)

    def test_options_bypasses_write_throttle(self):
        request = self.factory.options(
            "/api/v1/test/"
        )

        allowed = self.throttle.allow_request(
            request,
            self.view,
        )

        self.assertTrue(allowed)

class ApiV1ThrottleConfigurationTests(
    SimpleTestCase
):
    def test_ticket_purchase_view_uses_write_throttle(self):
        match = resolve(
            reverse(
                "api:v1-client-ticket-list"
            )
        )

        view_class = match.func.cls

        self.assertIn(
            UnsafeMethodScopedRateThrottle,
            view_class.throttle_classes,
        )

        self.assertEqual(
            view_class.throttle_scope,
            "ticket_purchase",
        )

    def test_vendor_inventory_uses_write_throttle(self):
        match = resolve(
            reverse(
                "api:v1-vendor-inventory-purchase-list"
            )
        )

        view_class = match.func.cls

        self.assertIn(
            UnsafeMethodScopedRateThrottle,
            view_class.throttle_classes,
        )

        self.assertEqual(
            view_class.throttle_scope,
            "vendor_inventory_purchase",
        )