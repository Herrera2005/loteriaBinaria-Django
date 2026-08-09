from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.lottery.models import DrawEvent, LotteryProduct


class PublicApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = LotteryProduct.objects.create(
            kind=LotteryProduct.Kind.OFFICIAL,
            code=LotteryProduct.Code.OCTAL,
            name="Octal",
            allowed_symbols="01234567",
            selection_count=4,
            is_active=True,
        )
        draw_at = timezone.now() + timedelta(days=1)
        cls.event = DrawEvent.objects.create(
            product=cls.product,
            name="Octal público",
            sales_open_at=timezone.now() - timedelta(hours=1),
            sales_close_at=DrawEvent.calculate_sales_close_at(draw_at),
            draw_at=draw_at,
            price_minor=100,
            prize_minor=50000,
            status=DrawEvent.Status.SALES_OPEN,
        )

    def test_product_collection_returns_json(self):
        response = self.client.get(reverse("api:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["code"], "OCTAL")

    def test_product_detail_returns_json(self):
        response = self.client.get(
            reverse("api:product_detail", kwargs={"pk": self.product.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["selection_count"], 4)

    def test_event_collection_is_public_and_excludes_drafts(self):
        DrawEvent.objects.create(
            product=self.product,
            name="Borrador privado",
            sales_open_at=timezone.now() + timedelta(days=2),
            sales_close_at=DrawEvent.calculate_sales_close_at(
                timezone.now() + timedelta(days=3)
            ),
            draw_at=timezone.now() + timedelta(days=3),
            price_minor=100,
            prize_minor=50000,
            status=DrawEvent.Status.DRAFT,
        )
        response = self.client.get(reverse("api:event_list"))
        names = [item["name"] for item in response.json()["results"]]
        self.assertIn("Octal público", names)
        self.assertNotIn("Borrador privado", names)

    def test_api_rejects_post(self):
        response = self.client.post(reverse("api:product_list"), {})
        self.assertEqual(response.status_code, 405)

    @override_settings(
        PUBLIC_API_CORS_ALLOWED_ORIGINS=("https://cliente.example",)
    )
    def test_cors_only_allows_configured_origin(self):
        response = self.client.get(
            reverse("api:product_list"),
            HTTP_ORIGIN="https://cliente.example",
        )
        self.assertEqual(
            response["Access-Control-Allow-Origin"],
            "https://cliente.example",
        )
        denied = self.client.get(
            reverse("api:product_list"),
            HTTP_ORIGIN="https://evil.example",
        )
        self.assertNotIn("Access-Control-Allow-Origin", denied)
