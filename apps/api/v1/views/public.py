from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.lottery.models import DrawEvent, DrawResult, LotteryProduct

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
    Eventos que pueden aparecer en superficies públicas.

    DRAFT queda deliberadamente excluido.
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


class PublicListAPIView(generics.ListAPIView):
    """
    Respuesta temporal de colección compatible con la API pública existente.

    B4 sustituirá esto por paginación DRF real:
    count / next / previous / results.
    """

    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset()
        )

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response(
            {
                "count": queryset.count(),
                "results": serializer.data,
            }
        )


class PublicProductListView(PublicListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        queryset = (
            LotteryProduct.objects
            .filter(is_active=True)
            .order_by("id")
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
            queryset = queryset.filter(kind=kind)

        return queryset


class PublicProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        return LotteryProduct.objects.filter(
            is_active=True,
        )


class PublicEventListView(PublicListAPIView):
    serializer_class = EventSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

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


class PublicResultListView(PublicListAPIView):
    serializer_class = ResultSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        queryset = (
            DrawResult.objects
            .select_related(
                "event",
                "event__product",
            )
            .order_by(
                "-published_at",
                "-id",
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