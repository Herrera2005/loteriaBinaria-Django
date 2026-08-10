from __future__ import annotations

from django.conf import settings
from django.http import HttpResponse


class PublicApiCorsMiddleware:
    """CORS restringido exclusivamente a endpoints públicos de lectura.

    No habilita credenciales entre orígenes y solo permite GET, HEAD
    y OPTIONS sobre la API pública.
    """

    PUBLIC_API_PREFIX = "/api/v1/public/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_public_api = request.path.startswith(
            self.PUBLIC_API_PREFIX
        )

        if (
            is_public_api
            and request.method == "OPTIONS"
        ):
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        if not is_public_api:
            return response

        origin = request.headers.get(
            "Origin",
            "",
        )

        allowed_origins = getattr(
            settings,
            "PUBLIC_API_CORS_ALLOWED_ORIGINS",
            (),
        )

        if (
            origin
            and origin in allowed_origins
        ):
            response[
                "Access-Control-Allow-Origin"
            ] = origin

            response["Vary"] = "Origin"

            response[
                "Access-Control-Allow-Methods"
            ] = "GET, HEAD, OPTIONS"

            response[
                "Access-Control-Allow-Headers"
            ] = "Accept, Content-Type"

            response[
                "Access-Control-Max-Age"
            ] = "86400"

        return response