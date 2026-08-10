from __future__ import annotations

from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from rest_framework import (
    generics,
    status,
)
from rest_framework.authentication import (
    TokenAuthentication,
)
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.finance.models import (
    Movement,
    Wallet,
)
from apps.lottery.models import (
    DrawEvent,
    Ticket,
)
from apps.lottery.services import purchase_ticket

from ..http import (
    parse_idempotency_key,
    raise_domain_validation_error,
)
from ..pagination import PublicApiPagination
from ..permissions import (
    HasActiveMode,
    IsClientMode,
    IsOperationalUser,
)
from ..query import (
    choice_query_param,
    positive_int_query_param,
)
from ..serializers.auth import AuthUserSerializer
from ..serializers.client import (
    ClientMovementSerializer,
    ClientTicketPurchaseSerializer,
    ClientTicketSerializer,
    ClientWalletSerializer,
)
from ..filters import StrictOrderingFilter
from ..throttles import (
    UnsafeMethodScopedRateThrottle,
)

CLIENT_PERMISSION_CLASSES = [
    IsAuthenticated,
    IsOperationalUser,
    HasActiveMode,
    IsClientMode,
]


class ClientProfileView(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = CLIENT_PERMISSION_CLASSES

    def get(self, request):
        return Response(
            {
                "user": AuthUserSerializer(
                    request.user
                ).data,
                "active_mode": request.active_mode,
            }
        )


class ClientWalletListView(
    generics.ListAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = CLIENT_PERMISSION_CLASSES

    serializer_class = ClientWalletSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            Wallet.objects
            .filter(
                user=self.request.user
            )
            .order_by(
                "currency",
                "id",
            )
        )


class ClientWalletDetailView(
    generics.RetrieveAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = CLIENT_PERMISSION_CLASSES

    serializer_class = ClientWalletSerializer

    def get_queryset(self):
        return Wallet.objects.filter(
            user=self.request.user
        )


class ClientTicketListView(
    generics.ListAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = CLIENT_PERMISSION_CLASSES

    throttle_classes = [
        UnsafeMethodScopedRateThrottle,
    ]
    throttle_scope = "ticket_purchase"

    serializer_class = ClientTicketSerializer
    pagination_class = PublicApiPagination

    filter_backends = [
        StrictOrderingFilter,
    ]

    ordering_fields = (
        "id",
        "created_at",
        "price_minor",
        "award_minor",
        "event__draw_at",
    )

    ordering = (
        "-created_at",
        "-id",
    )

    def get_queryset(self):
        queryset = (
            Ticket.objects
            .filter(
                user=self.request.user
            )
            .select_related(
                "event",
                "event__product",
            )
        )

        event_id = positive_int_query_param(
            self.request,
            "event",
        )

        product_id = positive_int_query_param(
            self.request,
            "product",
        )

        ownership_status = choice_query_param(
            self.request,
            "ownership_status",
            choices=(
                Ticket._meta
                .get_field("ownership_status")
                .choices
            ),
        )

        evaluation_status = choice_query_param(
            self.request,
            "evaluation_status",
            choices=(
                Ticket._meta
                .get_field("evaluation_status")
                .choices
            ),
        )

        if event_id is not None:
            queryset = queryset.filter(
                event_id=event_id
            )

        if product_id is not None:
            queryset = queryset.filter(
                event__product_id=product_id
            )

        if ownership_status is not None:
            queryset = queryset.filter(
                ownership_status=ownership_status
            )

        if evaluation_status is not None:
            queryset = queryset.filter(
                evaluation_status=evaluation_status
            )

        return queryset

    def post(self, request):
        input_serializer = (
            ClientTicketPurchaseSerializer(
                data=request.data
            )
        )

        input_serializer.is_valid(
            raise_exception=True
        )

        operation_id = parse_idempotency_key(
            request
        )

        event_id = (
            input_serializer
            .validated_data[
                "event_id"
            ]
        )

        symbols = (
            input_serializer
            .validated_data[
                "symbols"
            ]
        )

        try:
            ticket, created = purchase_ticket(
                user=request.user,
                active_mode=request.active_mode,
                event_id=event_id,
                combination=symbols,
                operation_id=operation_id,
            )
        except DrawEvent.DoesNotExist as exc:
            raise NotFound(
                "El evento solicitado no existe."
            ) from exc
        except DjangoValidationError as exc:
            raise_domain_validation_error(
                exc
            )

        output_serializer = (
            ClientTicketSerializer(
                ticket
            )
        )

        response_status = (
            status.HTTP_201_CREATED
            if created
            else status.HTTP_200_OK
        )

        return Response(
            {
                "created": created,
                "ticket": (
                    output_serializer.data
                ),
            },
            status=response_status,
        )


class ClientTicketDetailView(
    generics.RetrieveAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = CLIENT_PERMISSION_CLASSES

    serializer_class = ClientTicketSerializer

    def get_queryset(self):
        return (
            Ticket.objects
            .filter(
                user=self.request.user
            )
            .select_related(
                "event",
                "event__product",
            )
        )


class ClientMovementListView(
    generics.ListAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = CLIENT_PERMISSION_CLASSES

    serializer_class = ClientMovementSerializer
    pagination_class = PublicApiPagination

    filter_backends = [
        StrictOrderingFilter,
    ]

    ordering_fields = (
        "id",
        "created_at",
        "amount_minor",
        "balance_after_minor",
    )

    ordering = (
        "-created_at",
        "-id",
    )

    def get_queryset(self):
        queryset = (
            Movement.objects
            .filter(
                wallet__user=self.request.user
            )
            .select_related(
                "wallet",
            )
        )

        currency = choice_query_param(
            self.request,
            "currency",
            choices=(
                Wallet._meta
                .get_field("currency")
                .choices
            ),
        )

        movement_type = choice_query_param(
            self.request,
            "type",
            choices=(
                Movement._meta
                .get_field("type")
                .choices
            ),
        )

        direction = choice_query_param(
            self.request,
            "direction",
            choices=(
                Movement._meta
                .get_field("direction")
                .choices
            ),
        )

        if currency is not None:
            queryset = queryset.filter(
                wallet__currency=currency
            )

        if movement_type is not None:
            queryset = queryset.filter(
                type=movement_type
            )

        if direction is not None:
            queryset = queryset.filter(
                direction=direction
            )

        return queryset


class ClientMovementDetailView(
    generics.RetrieveAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = CLIENT_PERMISSION_CLASSES

    serializer_class = ClientMovementSerializer

    def get_queryset(self):
        return (
            Movement.objects
            .filter(
                wallet__user=self.request.user
            )
            .select_related(
                "wallet",
            )
        )