from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.lottery.models import DrawEvent, LotteryProduct


class ApiV1PaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = LotteryProduct.objects.create(
            kind=LotteryProduct.Kind.OFFICIAL,
            code=LotteryProduct.Code.OCTAL,
            name="Octal",
            allowed_symbols="01234567",
            selection_count=4,
            is_active=True,
            accent_color="#F5C542",
        )

        now = timezone.now()

        for index in range(25):
            draw_at = (
                now
                + timedelta(
                    days=index + 1,
                )
            )

            DrawEvent.objects.create(
                product=cls.product,
                name=f"Sorteo {index + 1:02d}",
                sales_open_at=now,
                draw_at=draw_at,
                price_minor=100,
                prize_minor=50000,
                status=DrawEvent.Status.SCHEDULED,
            )

    def test_event_list_uses_page_number_pagination(self):
        response = self.client.get(
            reverse("api:v1-public-event-list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["count"],
            25,
        )

        self.assertEqual(
            len(payload["results"]),
            20,
        )

        self.assertIsNotNone(
            payload["next"],
        )

        self.assertIsNone(
            payload["previous"],
        )

    def test_second_page_is_available(self):
        response = self.client.get(
            reverse("api:v1-public-event-list"),
            {
                "page": 2,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["count"],
            25,
        )

        self.assertEqual(
            len(payload["results"]),
            5,
        )

        self.assertIsNone(
            payload["next"],
        )

        self.assertIsNotNone(
            payload["previous"],
        )

    def test_page_size_can_be_reduced(self):
        response = self.client.get(
            reverse("api:v1-public-event-list"),
            {
                "page_size": 5,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["count"],
            25,
        )

        self.assertEqual(
            len(payload["results"]),
            5,
        )

    def test_page_size_cannot_exceed_maximum(self):
        response = self.client.get(
            reverse("api:v1-public-event-list"),
            {
                "page_size": 500,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["count"],
            25,
        )

        self.assertEqual(
            len(payload["results"]),
            25,
        )

    def test_invalid_page_returns_normalized_error(self):
        response = self.client.get(
            reverse("api:v1-public-event-list"),
            {
                "page": 999999,
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        payload = response.json()

        self.assertIn(
            "error",
            payload,
        )

        self.assertEqual(
            payload["error"]["code"],
            "NOT_FOUND",
        )

        self.assertIsInstance(
            payload["error"]["message"],
            str,
        )

        self.assertIsNone(
            payload["error"]["fields"],
        )

    def test_event_ordering_can_be_changed_explicitly(self):
        response = self.client.get(
            reverse("api:v1-public-event-list"),
            {
                "ordering": "draw_at",
                "page_size": 100,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.json()["results"]

        draw_dates = [
            item["draw_at"]
            for item in results
        ]

        self.assertEqual(
            draw_dates,
            sorted(draw_dates),
        )

    def test_event_default_order_is_latest_draw_first(self):
        response = self.client.get(
            reverse("api:v1-public-event-list"),
            {
                "page_size": 100,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.json()["results"]

        self.assertEqual(
            results[0]["name"],
            "Sorteo 25",
        )

        self.assertEqual(
            results[-1]["name"],
            "Sorteo 01",
        )

    def test_unknown_ordering_field_returns_bad_request(self):
        response = self.client.get(
            reverse(
                "api:v1-public-event-list"
            ),
            {
                "ordering": "campo_desconocido",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        payload = response.json()

        self.assertEqual(
            payload["error"]["code"],
            "BAD_REQUEST",
        )

        self.assertIn(
            "ordering",
            payload["error"]["fields"],
        )