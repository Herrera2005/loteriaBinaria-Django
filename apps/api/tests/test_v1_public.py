from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.lottery.models import (
    DrawEvent,
    DrawResult,
    LotteryProduct,
)


class ApiV1PublicTests(TestCase):
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

        cls.second_product = LotteryProduct.objects.create(
            kind=LotteryProduct.Kind.OFFICIAL,
            code=LotteryProduct.Code.DECIMAL,
            name="Decimal",
            allowed_symbols="0123456789",
            selection_count=5,
            is_active=True,
            accent_color="#38BDF8",
        )

        cls.inactive_product = LotteryProduct.objects.create(
            kind=LotteryProduct.Kind.CUSTOM,
            code="INACTIVO_TEST",
            name="Producto inactivo",
            allowed_symbols="ABCDEF",
            selection_count=3,
            is_active=False,
            accent_color="#6B7280",
        )

        now = timezone.now()

        cls.open_draw_at = now + timedelta(days=1)

        cls.open_event = DrawEvent.objects.create(
            product=cls.product,
            name="Octal público",
            sales_open_at=now - timedelta(hours=1),
            draw_at=cls.open_draw_at,
            price_minor=100,
            prize_minor=50000,
            status=DrawEvent.Status.SALES_OPEN,
        )

        cls.scheduled_draw_at = now + timedelta(days=2)

        cls.scheduled_event = DrawEvent.objects.create(
            product=cls.second_product,
            name="Decimal programado",
            sales_open_at=now + timedelta(hours=2),
            draw_at=cls.scheduled_draw_at,
            price_minor=250,
            prize_minor=100000,
            status=DrawEvent.Status.SCHEDULED,
        )

        cls.draft_draw_at = now + timedelta(days=3)

        cls.draft_event = DrawEvent.objects.create(
            product=cls.product,
            name="Borrador privado",
            sales_open_at=now + timedelta(days=2),
            draw_at=cls.draft_draw_at,
            price_minor=100,
            prize_minor=50000,
            status=DrawEvent.Status.DRAFT,
        )

        cls.finished_draw_at = now - timedelta(hours=1)

        cls.finished_event = DrawEvent.objects.create(
            product=cls.product,
            name="Octal finalizado",
            sales_open_at=now - timedelta(hours=4),
            draw_at=cls.finished_draw_at,
            price_minor=100,
            prize_minor=50000,
            status=DrawEvent.Status.FINISHED,
        )

        cls.result = DrawResult.objects.create(
            event=cls.finished_event,
            winning_key="0123",
            published_by=None,
            publication_source=DrawResult.PublicationSource.SYSTEM,
            reason="Resultado automático de prueba.",
        )

    def test_product_list_is_public_and_returns_expected_contract(self):
        response = self.client.get(
            reverse("api:v1-public-product-list")
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(payload["count"], 2)
        self.assertIn("results", payload)

        product = next(
            item
            for item in payload["results"]
            if item["code"] == "OCTAL"
        )

        self.assertEqual(
            set(product.keys()),
            {
                "id",
                "code",
                "name",
                "kind",
                "kind_label",
                "symbols",
                "selection_count",
                "accent_color",
                "is_active",
            },
        )

        self.assertEqual(product["id"], self.product.pk)
        self.assertEqual(product["code"], "OCTAL")
        self.assertEqual(product["name"], "Octal")
        self.assertEqual(product["kind"], "OFFICIAL")
        self.assertEqual(product["kind_label"], "Oficial")

        self.assertEqual(
            product["symbols"],
            [
                "0",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
            ],
        )

        self.assertEqual(
            product["selection_count"],
            4,
        )
        self.assertEqual(
            product["accent_color"],
            "#F5C542",
        )
        self.assertTrue(product["is_active"])

    def test_product_detail_returns_expected_contract(self):
        response = self.client.get(
            reverse(
                "api:v1-public-product-detail",
                kwargs={"pk": self.product.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(payload["id"], self.product.pk)
        self.assertEqual(payload["code"], "OCTAL")
        self.assertEqual(payload["selection_count"], 4)

        self.assertEqual(
            payload["symbols"],
            [
                "0",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
            ],
        )

    def test_inactive_products_are_not_public(self):
        response = self.client.get(
            reverse("api:v1-public-product-list")
        )

        self.assertEqual(response.status_code, 200)

        codes = {
            item["code"]
            for item in response.json()["results"]
        }

        self.assertIn("OCTAL", codes)
        self.assertIn("DECIMAL", codes)
        self.assertNotIn(
            self.inactive_product.code,
            codes,
        )

    def test_inactive_product_detail_returns_404(self):
        response = self.client.get(
            reverse(
                "api:v1-public-product-detail",
                kwargs={
                    "pk": self.inactive_product.pk,
                },
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_product_list_supports_name_filter(self):
        response = self.client.get(
            reverse("api:v1-public-product-list"),
            {
                "q": "Oct",
            },
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(payload["count"], 1)
        self.assertEqual(
            payload["results"][0]["code"],
            "OCTAL",
        )

    def test_product_list_supports_kind_filter_case_insensitively(self):
        response = self.client.get(
            reverse("api:v1-public-product-list"),
            {
                "kind": "official",
            },
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(payload["count"], 2)

        for item in payload["results"]:
            self.assertEqual(
                item["kind"],
                "OFFICIAL",
            )

    def test_unknown_product_kind_returns_bad_request(self):
        response = self.client.get(
            reverse(
                "api:v1-public-product-list"
            ),
            {
                "kind": "NO_EXISTE",
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
            "kind",
            payload["error"]["fields"],
        )

    def test_event_list_is_public_and_excludes_drafts(self):
        response = self.client.get(
            reverse("api:v1-public-event-list")
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        names = {
            item["name"]
            for item in payload["results"]
        }

        self.assertIn(
            self.open_event.name,
            names,
        )
        self.assertIn(
            self.scheduled_event.name,
            names,
        )
        self.assertIn(
            self.finished_event.name,
            names,
        )
        self.assertNotIn(
            self.draft_event.name,
            names,
        )

    def test_draft_event_detail_returns_404(self):
        response = self.client.get(
            reverse(
                "api:v1-public-event-detail",
                kwargs={"pk": self.draft_event.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_event_detail_returns_stable_contract(self):
        response = self.client.get(
            reverse(
                "api:v1-public-event-detail",
                kwargs={"pk": self.open_event.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(
            set(payload.keys()),
            {
                "id",
                "name",
                "product",
                "status",
                "status_label",
                "sales_open_at",
                "sales_close_at",
                "draw_at",
                "price",
                "prize",
                "is_open_now",
            },
        )

        self.assertEqual(
            payload["id"],
            self.open_event.pk,
        )
        self.assertEqual(
            payload["name"],
            "Octal público",
        )
        self.assertEqual(
            payload["status"],
            DrawEvent.Status.SALES_OPEN,
        )
        self.assertEqual(
            payload["status_label"],
            "Ventas abiertas",
        )

        self.assertEqual(
            payload["product"]["id"],
            self.product.pk,
        )
        self.assertEqual(
            payload["product"]["code"],
            "OCTAL",
        )

        self.assertEqual(
            payload["price"],
            {
                "minor": 100,
                "currency": "VIRTUAL",
                "display": "V 1.00",
            },
        )

        self.assertEqual(
            payload["prize"],
            {
                "minor": 50000,
                "currency": "VIRTUAL",
                "display": "V 500.00",
            },
        )

        self.assertTrue(
            payload["is_open_now"]
        )

    def test_event_list_supports_product_filter(self):
        response = self.client.get(
            reverse("api:v1-public-event-list"),
            {
                "product": self.product.pk,
            },
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertGreaterEqual(
            payload["count"],
            2,
        )

        for event in payload["results"]:
            self.assertEqual(
                event["product"]["id"],
                self.product.pk,
            )

    def test_event_list_supports_status_filter_case_insensitively(self):
        response = self.client.get(
            reverse("api:v1-public-event-list"),
            {
                "status": "sales_open",
            },
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(payload["count"], 1)

        self.assertEqual(
            payload["results"][0]["id"],
            self.open_event.pk,
        )

        self.assertEqual(
            payload["results"][0]["status"],
            DrawEvent.Status.SALES_OPEN,
        )

    def test_event_list_supports_name_filter(self):
        response = self.client.get(
            reverse("api:v1-public-event-list"),
            {
                "q": "Decimal",
            },
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(payload["count"], 1)
        self.assertEqual(
            payload["results"][0]["id"],
            self.scheduled_event.pk,
        )

    def test_unknown_event_status_returns_bad_request(self):
        response = self.client.get(
            reverse(
                "api:v1-public-event-list"
            ),
            {
                "status": "NO_EXISTE",
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
            "status",
            payload["error"]["fields"],
        )

    def test_event_datetimes_are_serialized(self):
        response = self.client.get(
            reverse(
                "api:v1-public-event-detail",
                kwargs={"pk": self.open_event.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertIsInstance(
            payload["sales_open_at"],
            str,
        )
        self.assertIsInstance(
            payload["sales_close_at"],
            str,
        )
        self.assertIsInstance(
            payload["draw_at"],
            str,
        )

    def test_result_list_is_public_and_returns_expected_contract(self):
        response = self.client.get(
            reverse("api:v1-public-result-list")
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(payload["count"], 1)
        self.assertEqual(
            len(payload["results"]),
            1,
        )

        result = payload["results"][0]

        self.assertEqual(
            set(result.keys()),
            {
                "id",
                "event",
                "winning_key",
                "winning_symbols",
                "publication_source",
                "publication_source_label",
                "published_at",
            },
        )

        self.assertEqual(
            result["id"],
            self.result.pk,
        )
        self.assertEqual(
            result["winning_key"],
            "0123",
        )
        self.assertEqual(
            result["winning_symbols"],
            [
                "0",
                "1",
                "2",
                "3",
            ],
        )

        self.assertEqual(
            result["publication_source"],
            DrawResult.PublicationSource.SYSTEM,
        )

        self.assertEqual(
            result["publication_source_label"],
            "Sistema",
        )

        self.assertEqual(
            result["event"]["id"],
            self.finished_event.pk,
        )

        self.assertEqual(
            result["event"]["product"]["code"],
            "OCTAL",
        )

    def test_result_detail_returns_expected_contract(self):
        response = self.client.get(
            reverse(
                "api:v1-public-result-detail",
                kwargs={"pk": self.result.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(
            payload["id"],
            self.result.pk,
        )
        self.assertEqual(
            payload["winning_key"],
            "0123",
        )
        self.assertEqual(
            payload["winning_symbols"],
            [
                "0",
                "1",
                "2",
                "3",
            ],
        )

        self.assertEqual(
            payload["event"]["name"],
            self.finished_event.name,
        )

    def test_result_list_supports_product_filter(self):
        response = self.client.get(
            reverse("api:v1-public-result-list"),
            {
                "product": self.product.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["count"],
            1,
        )

        response = self.client.get(
            reverse("api:v1-public-result-list"),
            {
                "product": self.second_product.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["count"],
            0,
        )

    def test_missing_public_details_return_404(self):
        cases = (
            (
                "api:v1-public-product-detail",
                999999,
            ),
            (
                "api:v1-public-event-detail",
                999999,
            ),
            (
                "api:v1-public-result-detail",
                999999,
            ),
        )

        for route_name, pk in cases:
            with self.subTest(
                route_name=route_name,
            ):
                response = self.client.get(
                    reverse(
                        route_name,
                        kwargs={"pk": pk},
                    )
                )

                self.assertEqual(
                    response.status_code,
                    404,
                )

    def test_public_collections_reject_post(self):
        route_names = (
            "api:v1-public-product-list",
            "api:v1-public-event-list",
            "api:v1-public-result-list",
        )

        for route_name in route_names:
            with self.subTest(
                route_name=route_name,
            ):
                response = self.client.post(
                    reverse(route_name),
                    data={},
                    content_type="application/json",
                )

                self.assertEqual(
                    response.status_code,
                    405,
                )

    def test_public_details_reject_put_patch_and_delete(self):
        cases = (
            (
                "api:v1-public-product-detail",
                self.product.pk,
            ),
            (
                "api:v1-public-event-detail",
                self.open_event.pk,
            ),
            (
                "api:v1-public-result-detail",
                self.result.pk,
            ),
        )

        for route_name, pk in cases:
            url = reverse(
                route_name,
                kwargs={"pk": pk},
            )

            with self.subTest(
                route_name=route_name,
                method="PUT",
            ):
                response = self.client.put(
                    url,
                    data={},
                    content_type="application/json",
                )

                self.assertEqual(
                    response.status_code,
                    405,
                )

            with self.subTest(
                route_name=route_name,
                method="PATCH",
            ):
                response = self.client.patch(
                    url,
                    data={},
                    content_type="application/json",
                )

                self.assertEqual(
                    response.status_code,
                    405,
                )

            with self.subTest(
                route_name=route_name,
                method="DELETE",
            ):
                response = self.client.delete(
                    url,
                )

                self.assertEqual(
                    response.status_code,
                    405,
                )

    def test_v1_public_contract_does_not_expose_private_result_fields(self):
        response = self.client.get(
            reverse(
                "api:v1-public-result-detail",
                kwargs={"pk": self.result.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertNotIn(
            "published_by",
            payload,
        )
        self.assertNotIn(
            "reason",
            payload,
        )

    def test_invalid_event_product_filter_returns_bad_request(self):
        response = self.client.get(
            reverse(
                "api:v1-public-event-list"
            ),
            {
                "product": "abc",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.json()["error"]["code"],
            "BAD_REQUEST",
        )

    def test_invalid_event_status_filter_returns_bad_request(self):
        response = self.client.get(
            reverse(
                "api:v1-public-event-list"
            ),
            {
                "status": "NO_EXISTE",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "status",
            response.json()["error"]["fields"],
        )

    def test_invalid_public_event_ordering_returns_bad_request(self):
        response = self.client.get(
            reverse(
                "api:v1-public-event-list"
            ),
            {
                "ordering": "password",
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

    def test_valid_public_event_ordering_is_accepted(self):
        response = self.client.get(
            reverse(
                "api:v1-public-event-list"
            ),
            {
                "ordering": "-draw_at",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )