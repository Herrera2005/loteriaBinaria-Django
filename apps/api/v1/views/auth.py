from __future__ import annotations

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from ..modes import (
    ACTIVE_MODE_HEADER,
    resolve_active_mode,
)
from ..serializers.auth import (
    ActiveModeSerializer,
    AuthUserSerializer,
    LoginSerializer,
)
from ..permissions import (
    HasActiveMode,
    IsOperationalUser,
)
from ..throttles import LoginRateThrottle


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [
        LoginRateThrottle,
    ]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        user = serializer.validated_data["user"]

        token, _ = Token.objects.get_or_create(
            user=user,
        )

        return Response(
            {
                "token": token.key,
                "user": AuthUserSerializer(
                    user
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        return Response(
            {
                "user": AuthUserSerializer(
                    request.user
                ).data,
            }
        )


class LogoutView(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        if request.auth is not None:
            request.auth.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

class ModeView(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
        IsOperationalUser,
    ]

    def get(self, request):
        resolution = resolve_active_mode(
            request.user,
            request.headers.get(
                ACTIVE_MODE_HEADER
            ),
        )

        serializer = ActiveModeSerializer(
            {
                "requested_mode": (
                    resolution.requested_mode
                ),
                "active_mode": (
                    resolution.active_mode
                ),
                "available_modes": list(
                    resolution.available_modes
                ),
            }
        )

        return Response(
            serializer.data
        )

class ContextView(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
        IsOperationalUser,
        HasActiveMode,
    ]

    def get(self, request):
        return Response(
            {
                "user": AuthUserSerializer(
                    request.user
                ).data,
                "active_mode": (
                    request.active_mode
                ),
            }
        )