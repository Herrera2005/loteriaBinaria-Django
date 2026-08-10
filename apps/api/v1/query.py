from __future__ import annotations

from collections.abc import Iterable

from rest_framework.exceptions import ValidationError


def _query_params(request):
    """
    Devuelve los parámetros GET tanto para Request de DRF
    como para WSGIRequest de Django.

    En producción las vistas DRF utilizan request.query_params.
    Las pruebas unitarias directas pueden utilizar request.GET.
    """
    query_params = getattr(
        request,
        "query_params",
        None,
    )

    if query_params is not None:
        return query_params

    return request.GET


def choice_query_param(
    request,
    name: str,
    *,
    choices: Iterable[tuple[str, str]],
) -> str | None:
    params = _query_params(request)

    raw_value = (
        params
        .get(name, "")
        .strip()
    )

    if not raw_value:
        return None

    normalized = raw_value.upper()

    valid_values = {
        str(value).upper(): value
        for value, _ in choices
    }

    if normalized not in valid_values:
        raise ValidationError(
            {
                name: [
                    "Valor de filtro no válido."
                ]
            }
        )

    return valid_values[normalized]


def positive_int_query_param(
    request,
    name: str,
) -> int | None:
    params = _query_params(request)

    raw_value = (
        params
        .get(name, "")
        .strip()
    )

    if not raw_value:
        return None

    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            {
                name: [
                    (
                        "Debe ser un identificador "
                        "entero positivo."
                    )
                ]
            }
        ) from exc

    if value <= 0:
        raise ValidationError(
            {
                name: [
                    (
                        "Debe ser un identificador "
                        "entero positivo."
                    )
                ]
            }
        )

    return value