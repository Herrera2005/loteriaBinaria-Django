from __future__ import annotations

from uuid import UUID

from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from rest_framework import (
    filters,
    generics,
    status,
)
from rest_framework.authentication import (
    TokenAuthentication,
)
from rest_framework.exceptions import (
    NotFound,
    ValidationError,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.finance.models import (
    Movement,
    Wallet,
)
from apps.lottery.models import DrawEvent, Ticket
from apps.lottery.services import purchase_ticket

from ..pagination import PublicApiPagination
from ..permissions import (
    HasActiveMode,
    IsClientMode,
    IsOperationalUser,
)
from ..serializers.auth import AuthUserSerializer
from ..serializers.client import (
    ClientMovementSerializer,
    ClientTicketPurchaseSerializer,
    ClientTicketSerializer,
    ClientWalletSerializer,
)


CLIENT_PERMISSION_CLASSES = [
    IsAuthenticated,
    IsOperationalUser,
    HasActiveMode,
    IsClientMode,
]


IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"


def _parse_idempotency_key(request) -> UUID:
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
    except (TypeError, ValueError, AttributeError) as exc:
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


def _raise_service_validation_error(
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

    serializer_class = ClientTicketSerializer
    pagination_class = PublicApiPagination

    filter_backends = [
        filters.OrderingFilter,
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

        event_id = (
            self.request.query_params
            .get(
                "event",
                "",
            )
            .strip()
        )

        product_id = (
            self.request.query_params
            .get(
                "product",
                "",
            )
            .strip()
        )

        ownership_status = (
            self.request.query_params
            .get(
                "ownership_status",
                "",
            )
            .strip()
            .upper()
        )

        evaluation_status = (
            self.request.query_params
            .get(
                "evaluation_status",
                "",
            )
            .strip()
            .upper()
        )

        if event_id.isdigit():
            queryset = queryset.filter(
                event_id=int(
                    event_id
                )
            )

        if product_id.isdigit():
            queryset = queryset.filter(
                event__product_id=int(
                    product_id
                )
            )

        valid_ownership_statuses = {
            choice
            for choice, _ in (
                Ticket._meta
                .get_field(
                    "ownership_status"
                )
                .choices
            )
        }

        if (
            ownership_status
            in valid_ownership_statuses
        ):
            queryset = queryset.filter(
                ownership_status=(
                    ownership_status
                )
            )

        valid_evaluation_statuses = {
            choice
            for choice, _ in (
                Ticket._meta
                .get_field(
                    "evaluation_status"
                )
                .choices
            )
        }

        if (
            evaluation_status
            in valid_evaluation_statuses
        ):
            queryset = queryset.filter(
                evaluation_status=(
                    evaluation_status
                )
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

        operation_id = (
            _parse_idempotency_key(
                request
            )
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
            _raise_service_validation_error(
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
        filters.OrderingFilter,
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

        currency = (
            self.request.query_params
            .get(
                "currency",
                "",
            )
            .strip()
            .upper()
        )

        movement_type = (
            self.request.query_params
            .get(
                "type",
                "",
            )
            .strip()
            .upper()
        )

        direction = (
            self.request.query_params
            .get(
                "direction",
                "",
            )
            .strip()
            .upper()
        )

        valid_currencies = {
            choice
            for choice, _ in (
                Wallet._meta
                .get_field(
                    "currency"
                )
                .choices
            )
        }

        valid_types = {
            choice
            for choice, _ in (
                Movement._meta
                .get_field(
                    "type"
                )
                .choices
            )
        }

        valid_directions = {
            choice
            for choice, _ in (
                Movement._meta
                .get_field(
                    "direction"
                )
                .choices
            )
        }

        if currency in valid_currencies:
            queryset = queryset.filter(
                wallet__currency=currency
            )

        if movement_type in valid_types:
            queryset = queryset.filter(
                type=movement_type
            )

        if direction in valid_directions:
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