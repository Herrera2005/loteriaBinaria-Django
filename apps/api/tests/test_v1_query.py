from __future__ import annotations

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apps.api.v1.query import (
    choice_query_param,
    positive_int_query_param,
)


class ApiV1QueryHelperTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_missing_choice_returns_none(self):
        request = self.factory.get(
            "/test/"
        )

        self.assertIsNone(
            choice_query_param(
                request,
                "status",
                choices=(
                    ("ACTIVE", "Activo"),
                    ("DISABLED", "Desactivado"),
                ),
            )
        )

    def test_choice_is_case_insensitive(self):
        request = self.factory.get(
            "/test/",
            {
                "status": "active",
            },
        )

        self.assertEqual(
            choice_query_param(
                request,
                "status",
                choices=(
                    ("ACTIVE", "Activo"),
                    ("DISABLED", "Desactivado"),
                ),
            ),
            "ACTIVE",
        )

    def test_invalid_choice_is_rejected(self):
        request = self.factory.get(
            "/test/",
            {
                "status": "NO_EXISTE",
            },
        )

        with self.assertRaises(
            ValidationError
        ) as context:
            choice_query_param(
                request,
                "status",
                choices=(
                    ("ACTIVE", "Activo"),
                ),
            )

        self.assertIn(
            "status",
            context.exception.detail,
        )

    def test_missing_integer_returns_none(self):
        request = self.factory.get(
            "/test/"
        )

        self.assertIsNone(
            positive_int_query_param(
                request,
                "product",
            )
        )

    def test_valid_integer_is_returned(self):
        request = self.factory.get(
            "/test/",
            {
                "product": "42",
            },
        )

        self.assertEqual(
            positive_int_query_param(
                request,
                "product",
            ),
            42,
        )

    def test_non_integer_is_rejected(self):
        request = self.factory.get(
            "/test/",
            {
                "product": "abc",
            },
        )

        with self.assertRaises(
            ValidationError
        ):
            positive_int_query_param(
                request,
                "product",
            )

    def test_zero_is_rejected(self):
        request = self.factory.get(
            "/test/",
            {
                "product": "0",
            },
        )

        with self.assertRaises(
            ValidationError
        ):
            positive_int_query_param(
                request,
                "product",
            )

    def test_negative_integer_is_rejected(self):
        request = self.factory.get(
            "/test/",
            {
                "product": "-5",
            },
        )

        with self.assertRaises(
            ValidationError
        ):
            positive_int_query_param(
                request,
                "product",
            )