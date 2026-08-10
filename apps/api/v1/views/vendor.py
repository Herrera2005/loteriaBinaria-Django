from __future__ import annotations
from ..http import (
    parse_idempotency_key,
    raise_domain_validation_error,
)
from rest_framework import (
    generics,
    status,
)
from rest_framework.authentication import (
    TokenAuthentication,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from ..throttles import (
    UnsafeMethodScopedRateThrottle,
)

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
from ..query import choice_query_param
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from ..filters import StrictOrderingFilter

VENDOR_PERMISSION_CLASSES = [
    IsAuthenticated,
    IsOperationalUser,
    HasActiveMode,
    IsVendorMode,
    HasActiveVendorProfile,
]


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
        StrictOrderingFilter,
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

    throttle_classes = [
        UnsafeMethodScopedRateThrottle,
    ]
    throttle_scope = "vendor_conversion_action"

    def post(self, request, pk):
        try:
            assignment = assign_conversion_request(
                vendor=request.user,
                request_id=pk,
            )
        except DjangoValidationError as exc:
            raise_domain_validation_error(
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

    throttle_classes = [
        UnsafeMethodScopedRateThrottle,
    ]
    throttle_scope = "vendor_conversion_action"

    def post(self, request, pk):
        try:
            assignment, completed_now = (
                complete_conversion_request(
                    vendor=request.user,
                    assignment_id=pk,
                )
            )
        except DjangoValidationError as exc:
            raise_domain_validation_error(
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

    throttle_classes = [
        UnsafeMethodScopedRateThrottle,
    ]
    throttle_scope = "vendor_conversion_action"

    def post(self, request, pk):
        try:
            assignment, released_now = (
                release_conversion_assignment(
                    vendor=request.user,
                    assignment_id=pk,
                )
            )
        except DjangoValidationError as exc:
            raise_domain_validation_error(
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

    throttle_classes = [
        UnsafeMethodScopedRateThrottle,
    ]
    throttle_scope = "vendor_inventory_purchase"

    serializer_class = (
        VendorInventoryPurchaseSerializer
    )
    pagination_class = PublicApiPagination

    filter_backends = [
        StrictOrderingFilter,
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
            parse_idempotency_key(
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
            raise_domain_validation_error(
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