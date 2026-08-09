from __future__ import annotations

from collections.abc import Mapping

from rest_framework import status
from rest_framework.views import exception_handler


DEFAULT_ERROR_CODES = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "AUTHENTICATION_REQUIRED",
    status.HTTP_403_FORBIDDEN: "PERMISSION_DENIED",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    status.HTTP_429_TOO_MANY_REQUESTS: "THROTTLED",
}


DEFAULT_ERROR_MESSAGES = {
    status.HTTP_400_BAD_REQUEST: "La solicitud contiene datos inválidos.",
    status.HTTP_401_UNAUTHORIZED: "Se requiere autenticación.",
    status.HTTP_403_FORBIDDEN: "No tienes permiso para realizar esta acción.",
    status.HTTP_404_NOT_FOUND: "No encontrado.",
    status.HTTP_405_METHOD_NOT_ALLOWED: "Método no permitido.",
    status.HTTP_429_TOO_MANY_REQUESTS: "Demasiadas solicitudes. Inténtalo más tarde.",
}


def _extract_message(data) -> str:
    if isinstance(data, Mapping):
        detail = data.get("detail")

        if detail:
            return str(detail)

        return "La solicitud contiene datos inválidos."

    if isinstance(data, list) and data:
        return str(data[0])

    if data:
        return str(data)

    return "Ocurrió un error al procesar la solicitud."


def api_exception_handler(exc, context):
    """
    Normaliza las excepciones manejadas por Django REST Framework.

    Contrato:

    {
        "error": {
            "code": "...",
            "message": "...",
            "fields": null | {...}
        }
    }

    Los errores HTTP conocidos utilizan mensajes públicos estables para
    no exponer nombres internos de modelos, consultas o implementación.
    """

    response = exception_handler(exc, context)

    if response is None:
        return None

    original_data = response.data

    error_code = DEFAULT_ERROR_CODES.get(
        response.status_code,
        "API_ERROR",
    )

    message = DEFAULT_ERROR_MESSAGES.get(
        response.status_code,
    )

    if message is None:
        message = _extract_message(original_data)

    fields = None

    if (
        response.status_code == status.HTTP_400_BAD_REQUEST
        and isinstance(original_data, Mapping)
        and "detail" not in original_data
    ):
        fields = original_data

    response.data = {
        "error": {
            "code": error_code,
            "message": message,
            "fields": fields,
        }
    }

    return response