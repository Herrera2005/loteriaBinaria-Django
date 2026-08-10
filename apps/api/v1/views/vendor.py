from __future__ import annotations
from uuid import UUID
from rest_framework import (
    filters,
    generics,
    status,
)
from rest_framework.authentication import (
    TokenAuthentication,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from apps.finance.models import (
    Movement,
    VendorInventoryPurchase,
    Wallet,
)
from apps.finance.services import (
    purchase_vendor_inventory,
)
from apps.vendors.models import ConversionAssignment
from apps.vendors.services import (
    assign_conversion_request,
    complete_conversion_request,
    eligible_conversion_requests,
    release_conversion_assignment,
)

from ..pagination import PublicApiPagination
from ..permissions import (
    HasActiveMode,
    HasActiveVendorProfile,
    IsOperationalUser,
    IsVendorMode,
)
from ..serializers.auth import AuthUserSerializer
from ..serializers.vendor import (
    VendorAssignmentSerializer,
    VendorConversionRequestSerializer,
    VendorInventoryPurchaseInputSerializer,
    VendorInventoryPurchaseSerializer,
    VendorMovementSerializer,
    VendorProfileSerializer,
    VendorWalletSerializer,
)
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)

VENDOR_PERMISSION_CLASSES = [
    IsAuthenticated,
    IsOperationalUser,
    HasActiveMode,
    IsVendorMode,
    HasActiveVendorProfile,
]

def _raise_vendor_service_error(
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

def _fresh_assignment(
    assignment_id: int,
) -> ConversionAssignment:
    return (
        ConversionAssignment.objects
        .select_related(
            "request",
        )
        .get(
            pk=assignment_id
        )
    )

def _parse_vendor_idempotency_key(
    request,
) -> UUID:
    raw_value = request.headers.get(
        "Idempotency-Key",
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

class VendorProfileView(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = VENDOR_PERMISSION_CLASSES

    def get(self, request):
        return Response(
            {
                "user": AuthUserSerializer(
                    request.user
                ).data,
                "active_mode": request.active_mode,
                "vendor_profile": (
                    VendorProfileSerializer(
                        request.vendor_profile
                    ).data
                ),
            }
        )


class VendorWalletListView(
    generics.ListAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = VENDOR_PERMISSION_CLASSES

    serializer_class = VendorWalletSerializer
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


class VendorWalletDetailView(
    generics.RetrieveAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = VENDOR_PERMISSION_CLASSES

    serializer_class = VendorWalletSerializer

    def get_queryset(self):
        return Wallet.objects.filter(
            user=self.request.user
        )


class VendorMovementListView(
    generics.ListAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = VENDOR_PERMISSION_CLASSES

    serializer_class = VendorMovementSerializer
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
            .get("currency", "")
            .strip()
            .upper()
        )

        movement_type = (
            self.request.query_params
            .get("type", "")
            .strip()
            .upper()
        )

        direction = (
            self.request.query_params
            .get("direction", "")
            .strip()
            .upper()
        )

        valid_currencies = {
            value
            for value, _ in (
                Wallet._meta
                .get_field("currency")
                .choices
            )
        }

        valid_types = {
            value
            for value, _ in (
                Movement._meta
                .get_field("type")
                .choices
            )
        }

        valid_directions = {
            value
            for value, _ in (
                Movement._meta
                .get_field("direction")
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


class VendorMovementDetailView(
    generics.RetrieveAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = VENDOR_PERMISSION_CLASSES

    serializer_class = VendorMovementSerializer

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


class VendorAvailableRequestListView(
    generics.ListAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = VENDOR_PERMISSION_CLASSES

    serializer_class = VendorConversionRequestSerializer
    pagination_class = PublicApiPagination

    def get_queryset(self):
        return eligible_conversion_requests(
            vendor=self.request.user
        )


class VendorAssignmentListView(
    generics.ListAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = VENDOR_PERMISSION_CLASSES

    serializer_class = VendorAssignmentSerializer
    pagination_class = PublicApiPagination

    filter_backends = [
        filters.OrderingFilter,
    ]

    ordering_fields = (
        "id",
        "assigned_at",
        "released_at",
        "completed_at",
    )

    ordering = (
        "-assigned_at",
        "-id",
    )

    def get_queryset(self):
        return (
            ConversionAssignment.objects
            .filter(
                vendor=self.request.vendor_profile
            )
            .select_related(
                "request",
            )
        )


class VendorAssignmentDetailView(
    generics.RetrieveAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = VENDOR_PERMISSION_CLASSES

    serializer_class = VendorAssignmentSerializer

    def get_queryset(self):
        return (
            ConversionAssignment.objects
            .filter(
                vendor=self.request.vendor_profile
            )
            .select_related(
                "request",
            )
        )

class VendorAssignRequestView(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = VENDOR_PERMISSION_CLASSES

    def post(self, request, pk):
        try:
            assignment = assign_conversion_request(
                vendor=request.user,
                request_id=pk,
            )
        except DjangoValidationError as exc:
            _raise_vendor_service_error(
                exc
            )

        assignment = _fresh_assignment(
            assignment.pk
        )

        return Response(
            {
                "created": True,
                "assignment": (
                    VendorAssignmentSerializer(
                        assignment
                    ).data
                ),
            },
            status=status.HTTP_201_CREATED,
        )

class VendorCompleteAssignmentView(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = VENDOR_PERMISSION_CLASSES

    def post(self, request, pk):
        try:
            assignment, completed_now = (
                complete_conversion_request(
                    vendor=request.user,
                    assignment_id=pk,
                )
            )
        except DjangoValidationError as exc:
            _raise_vendor_service_error(
                exc
            )

        assignment = _fresh_assignment(
            assignment.pk
        )

        return Response(
            {
                "completed_now": completed_now,
                "assignment": (
                    VendorAssignmentSerializer(
                        assignment
                    ).data
                ),
            },
            status=status.HTTP_200_OK,
        )

class VendorReleaseAssignmentView(APIView):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = VENDOR_PERMISSION_CLASSES

    def post(self, request, pk):
        try:
            assignment, released_now = (
                release_conversion_assignment(
                    vendor=request.user,
                    assignment_id=pk,
                )
            )
        except DjangoValidationError as exc:
            _raise_vendor_service_error(
                exc
            )

        assignment = _fresh_assignment(
            assignment.pk
        )

        return Response(
            {
                "released_now": released_now,
                "assignment": (
                    VendorAssignmentSerializer(
                        assignment
                    ).data
                ),
            },
            status=status.HTTP_200_OK,
        )

class VendorInventoryPurchaseListView(
    generics.ListAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = VENDOR_PERMISSION_CLASSES

    serializer_class = (
        VendorInventoryPurchaseSerializer
    )
    pagination_class = PublicApiPagination

    filter_backends = [
        filters.OrderingFilter,
    ]

    ordering_fields = (
        "id",
        "created_at",
        "amount_minor",
        "cost_real_minor",
    )

    ordering = (
        "-created_at",
        "-id",
    )

    def get_queryset(self):
        return (
            VendorInventoryPurchase.objects
            .filter(
                user=self.request.user
            )
        )

    def post(self, request):
        input_serializer = (
            VendorInventoryPurchaseInputSerializer(
                data=request.data
            )
        )

        input_serializer.is_valid(
            raise_exception=True
        )

        operation_id = (
            _parse_vendor_idempotency_key(
                request
            )
        )

        try:
            purchase, created = (
                purchase_vendor_inventory(
                    vendor=request.user,
                    virtual_minor=(
                        input_serializer
                        .validated_data[
                            "virtual_minor"
                        ]
                    ),
                    operation_id=operation_id,
                )
            )
        except DjangoValidationError as exc:
            _raise_vendor_service_error(
                exc
            )

        response_status = (
            status.HTTP_201_CREATED
            if created
            else status.HTTP_200_OK
        )

        return Response(
            {
                "created": created,
                "purchase": (
                    VendorInventoryPurchaseSerializer(
                        purchase
                    ).data
                ),
            },
            status=response_status,
        )


class VendorInventoryPurchaseDetailView(
    generics.RetrieveAPIView
):
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = VENDOR_PERMISSION_CLASSES

    serializer_class = (
        VendorInventoryPurchaseSerializer
    )

    def get_queryset(self):
        return (
            VendorInventoryPurchase.objects
            .filter(
                user=self.request.user
            )
        )