from django.test import TestCase
from django.urls import reverse


class ApiV1FoundationTests(TestCase):
    def test_health_is_public_and_returns_expected_contract(self):
        response = self.client.get(reverse("api:v1-health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "service": "loteria-binaria-api",
                "version": "v1",
            },
        )

    def test_health_rejects_post(self):
        response = self.client.post(
            reverse("api:v1-health"),
            data={},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 405)