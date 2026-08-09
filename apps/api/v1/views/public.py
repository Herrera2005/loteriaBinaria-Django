from __future__ import annotations

from rest_framework import filters, generics
from rest_framework.permissions import AllowAny

from apps.lottery.models import DrawEvent, DrawResult, LotteryProduct

from ..pagination import PublicApiPagination
from ..serializers.public import (
    EventSerializer,
    ProductSerializer,
    ResultSerializer,
)


PUBLIC_EVENT_STATUSES = (
    DrawEvent.Status.SCHEDULED,
    DrawEvent.Status.PUBLISHED,
    DrawEvent.Status.SALES_OPEN,
    DrawEvent.Status.SALES_CLOSED,
    DrawEvent.Status.RESULT_SET,
    DrawEvent.Status.FINISHED,
    DrawEvent.Status.CANCELLED,
)


def public_events_queryset():
    """
    QuerySet base de eventos visibles públicamente.

    Los eventos DRAFT nunca forman parte de la API pública.
    """
    return (
        DrawEvent.objects
        .filter(
            product__is_active=True,
            status__in=PUBLIC_EVENT_STATUSES,
        )
        .select_related("product")
        .order_by("-draw_at", "-id")
    )


class PublicProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = PublicApiPagination

    filter_backends = [
        filters.OrderingFilter,
    ]

    ordering_fields = (
        "id",
        "name",
        "code",
    )

    ordering = (
        "id",
    )

    def get_queryset(self):
        queryset = (
            LotteryProduct.objects
            .filter(is_active=True)
        )

        query = self.request.query_params.get(
            "q",
            "",
        ).strip()

        kind = self.request.query_params.get(
            "kind",
            "",
        ).strip().upper()

        if query:
            queryset = queryset.filter(
                name__icontains=query,
            )

        valid_kinds = {
            choice
            for choice, _ in LotteryProduct.Kind.choices
        }

        if kind in valid_kinds:
            queryset = queryset.filter(
                kind=kind,
            )

        return queryset


class PublicProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        return LotteryProduct.objects.filter(
            is_active=True,
        )


class PublicEventListView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = PublicApiPagination

    filter_backends = [
        filters.OrderingFilter,
    ]

    ordering_fields = (
        "id",
        "name",
        "draw_at",
        "sales_open_at",
        "sales_close_at",
        "price_minor",
        "prize_minor",
    )

    ordering = (
        "-draw_at",
        "-id",
    )

    def get_queryset(self):
        queryset = public_events_queryset()

        product_id = self.request.query_params.get(
            "product",
            "",
        ).strip()

        status = self.request.query_params.get(
            "status",
            "",
        ).strip().upper()

        query = self.request.query_params.get(
            "q",
            "",
        ).strip()

        if product_id.isdigit():
            queryset = queryset.filter(
                product_id=int(product_id),
            )

        valid_statuses = {
            choice
            for choice, _ in DrawEvent.Status.choices
        }

        if status in valid_statuses:
            queryset = queryset.filter(
                status=status,
            )

        if query:
            queryset = queryset.filter(
                name__icontains=query,
            )

        return queryset


class PublicEventDetailView(generics.RetrieveAPIView):
    serializer_class = EventSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        return public_events_queryset()


class PublicResultListView(generics.ListAPIView):
    serializer_class = ResultSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = PublicApiPagination

    filter_backends = [
        filters.OrderingFilter,
    ]

    ordering_fields = (
        "id",
        "published_at",
        "event__draw_at",
    )

    ordering = (
        "-published_at",
        "-id",
    )

    def get_queryset(self):
        queryset = (
            DrawResult.objects
            .select_related(
                "event",
                "event__product",
            )
        )

        product_id = self.request.query_params.get(
            "product",
            "",
        ).strip()

        if product_id.isdigit():
            queryset = queryset.filter(
                event__product_id=int(product_id),
            )

        return queryset


class PublicResultDetailView(generics.RetrieveAPIView):
    serializer_class = ResultSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        return (
            DrawResult.objects
            .select_related(
                "event",
                "event__product",
            )
        )