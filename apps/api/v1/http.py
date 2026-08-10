from __future__ import annotations

from uuid import UUID

from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from rest_framework.exceptions import ValidationError


IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"


def parse_idempotency_key(request) -> UUID:
    raw_value = request.headers.get(
        IDEMPOTENCY_KEY_HEADER,
        "",
    ).strip()

    if not raw_value:
        raise ValidationError(
            {
                "idempotency_key": [
                    (
                        "Debe enviar el encabezado "
                        "Idempotency-Key con un UUID válido."
                    )
                ]
            }
        )

    try:
        return UUID(raw_value)
    except (
        TypeError,
        ValueError,
        AttributeError,
    ) as exc:
        raise ValidationError(
            {
                "idempotency_key": [
                    (
                        "El encabezado Idempotency-Key "
                        "debe contener un UUID válido."
                    )
                ]
            }
        ) from exc


def raise_domain_validation_error(
    exc: DjangoValidationError,
) -> None:
    if hasattr(exc, "message_dict"):
        raise ValidationError(
            exc.message_dict
        ) from exc

    messages = getattr(
        exc,
        "messages",
        None,
    )

    if messages:
        raise ValidationError(
            {
                "non_field_errors": list(
                    messages
                )
            }
        ) from exc

    raise ValidationError(
        {
            "non_field_errors": [
                str(exc)
            ]
        }
    ) from exc