from django.test import TestCase
from django.urls import reverse


class ApiV1ErrorContractTests(TestCase):
    def test_missing_product_returns_normalized_404(self):
        response = self.client.get(
            reverse(
                "api:v1-public-product-detail",
                kwargs={
                    "pk": 999999,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "No encontrado.",
                    "fields": None,
                }
            },
        )

    def test_post_on_read_only_collection_returns_normalized_405(self):
        response = self.client.post(
            reverse(
                "api:v1-public-product-list"
            ),
            data={},
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            405,
        )

        payload = response.json()

        self.assertEqual(
            payload["error"]["code"],
            "METHOD_NOT_ALLOWED",
        )

        self.assertIsInstance(
            payload["error"]["message"],
            str,
        )

        self.assertIsNone(
            payload["error"]["fields"],
        )