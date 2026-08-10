from __future__ import annotations

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from apps.api.v1.filters import StrictOrderingFilter


class DummyRequest:
    query_params = {}


class DummyView:
    ordering_fields = (
        "id",
        "created_at",
        "amount_minor",
    )


class DummyQueryset:
    model = None


class ApiV1StrictOrderingFilterTests(
    SimpleTestCase
):
    def setUp(self):
        self.backend = StrictOrderingFilter()
        self.view = DummyView()
        self.request = DummyRequest()

    def test_valid_ascending_field_is_allowed(self):
        result = self.backend.remove_invalid_fields(
            DummyQueryset(),
            ["created_at"],
            self.view,
            self.request,
        )

        self.assertEqual(
            result,
            ["created_at"],
        )

    def test_valid_descending_field_is_allowed(self):
        result = self.backend.remove_invalid_fields(
            DummyQueryset(),
            ["-created_at"],
            self.view,
            self.request,
        )

        self.assertEqual(
            result,
            ["-created_at"],
        )

    def test_multiple_valid_fields_are_allowed(self):
        result = self.backend.remove_invalid_fields(
            DummyQueryset(),
            [
                "-created_at",
                "id",
            ],
            self.view,
            self.request,
        )

        self.assertEqual(
            result,
            [
                "-created_at",
                "id",
            ],
        )

    def test_invalid_field_is_rejected(self):
        with self.assertRaises(
            ValidationError
        ) as context:
            self.backend.remove_invalid_fields(
                DummyQueryset(),
                ["password"],
                self.view,
                self.request,
            )

        self.assertIn(
            "ordering",
            context.exception.detail,
        )

    def test_one_invalid_field_rejects_entire_ordering(self):
        with self.assertRaises(
            ValidationError
        ):
            self.backend.remove_invalid_fields(
                DummyQueryset(),
                [
                    "-created_at",
                    "pepito",
                ],
                self.view,
                self.request,
            )