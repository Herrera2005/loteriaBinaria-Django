from __future__ import annotations

import uuid

from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apps.api.v1.http import (
    parse_idempotency_key,
    raise_domain_validation_error,
)


class ApiV1HttpHelperTests(
    SimpleTestCase
):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_valid_idempotency_key_returns_uuid(self):
        operation_id = uuid.uuid4()

        request = self.factory.post(
            "/api/v1/test/",
            {},
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(
                operation_id
            ),
        )

        self.assertEqual(
            parse_idempotency_key(
                request
            ),
            operation_id,
        )

    def test_missing_idempotency_key_is_rejected(self):
        request = self.factory.post(
            "/api/v1/test/",
            {},
            format="json",
        )

        with self.assertRaises(
            ValidationError
        ) as context:
            parse_idempotency_key(
                request
            )

        self.assertIn(
            "idempotency_key",
            context.exception.detail,
        )

    def test_invalid_idempotency_key_is_rejected(self):
        request = self.factory.post(
            "/api/v1/test/",
            {},
            format="json",
            HTTP_IDEMPOTENCY_KEY=(
                "uuid-invalido"
            ),
        )

        with self.assertRaises(
            ValidationError
        ) as context:
            parse_idempotency_key(
                request
            )

        self.assertIn(
            "idempotency_key",
            context.exception.detail,
        )

    def test_domain_validation_messages_are_translated(self):
        original = DjangoValidationError(
            "Operación inválida."
        )

        with self.assertRaises(
            ValidationError
        ) as context:
            raise_domain_validation_error(
                original
            )

        self.assertIn(
            "non_field_errors",
            context.exception.detail,
        )

    def test_domain_validation_message_dict_is_preserved(self):
        original = DjangoValidationError(
            {
                "amount": [
                    "Monto inválido."
                ]
            }
        )

        with self.assertRaises(
            ValidationError
        ) as context:
            raise_domain_validation_error(
                original
            )

        self.assertIn(
            "amount",
            context.exception.detail,
        )