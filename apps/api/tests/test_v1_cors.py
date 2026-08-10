from __future__ import annotations

from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    PUBLIC_API_CORS_ALLOWED_ORIGINS=(
        "https://cliente.example",
    )
)
class ApiV1CorsTests(TestCase):
    def test_public_api_allows_configured_origin(self):
        response = self.client.get(
            reverse(
                "api:v1-public-product-list"
            ),
            HTTP_ORIGIN=(
                "https://cliente.example"
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response[
                "Access-Control-Allow-Origin"
            ],
            "https://cliente.example",
        )

        self.assertEqual(
            response[
                "Access-Control-Allow-Methods"
            ],
            "GET, HEAD, OPTIONS",
        )

        self.assertEqual(
            response[
                "Access-Control-Allow-Headers"
            ],
            "Accept, Content-Type",
        )

    def test_public_api_rejects_unconfigured_origin(self):
        response = self.client.get(
            reverse(
                "api:v1-public-product-list"
            ),
            HTTP_ORIGIN=(
                "https://evil.example"
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotIn(
            "Access-Control-Allow-Origin",
            response,
        )

    def test_public_api_preflight_returns_204(self):
        response = self.client.options(
            reverse(
                "api:v1-public-product-list"
            ),
            HTTP_ORIGIN=(
                "https://cliente.example"
            ),
            HTTP_ACCESS_CONTROL_REQUEST_METHOD=(
                "GET"
            ),
        )

        self.assertEqual(
            response.status_code,
            204,
        )

        self.assertEqual(
            response[
                "Access-Control-Allow-Origin"
            ],
            "https://cliente.example",
        )

    def test_auth_api_does_not_receive_public_cors_headers(self):
        response = self.client.options(
            reverse(
                "api:v1-auth-login"
            ),
            HTTP_ORIGIN=(
                "https://cliente.example"
            ),
            HTTP_ACCESS_CONTROL_REQUEST_METHOD=(
                "POST"
            ),
        )

        self.assertNotIn(
            "Access-Control-Allow-Origin",
            response,
        )

        self.assertNotIn(
            "Access-Control-Allow-Methods",
            response,
        )

    def test_client_api_does_not_receive_public_cors_headers(self):
        response = self.client.options(
            reverse(
                "api:v1-client-profile"
            ),
            HTTP_ORIGIN=(
                "https://cliente.example"
            ),
            HTTP_ACCESS_CONTROL_REQUEST_METHOD=(
                "GET"
            ),
        )

        self.assertNotIn(
            "Access-Control-Allow-Origin",
            response,
        )

    def test_vendor_api_does_not_receive_public_cors_headers(self):
        response = self.client.options(
            reverse(
                "api:v1-vendor-profile"
            ),
            HTTP_ORIGIN=(
                "https://cliente.example"
            ),
            HTTP_ACCESS_CONTROL_REQUEST_METHOD=(
                "GET"
            ),
        )

        self.assertNotIn(
            "Access-Control-Allow-Origin",
            response,
        )