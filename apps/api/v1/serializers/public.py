from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.finance.models import Wallet
from apps.lottery.models import (
    DrawEvent,
    DrawResult,
    LotteryProduct,
)

from ..money import money_data


class ProductSerializer(serializers.ModelSerializer):
    """
    Contrato público de LotteryProduct.

    Mantiene la misma estructura expuesta actualmente por la API pública
    heredada, pero utilizando Django REST Framework.
    """

    kind_label = serializers.CharField(
        source="get_kind_display",
        read_only=True,
    )

    symbols = serializers.SerializerMethodField()

    class Meta:
        model = LotteryProduct
        fields = (
            "id",
            "code",
            "name",
            "kind",
            "kind_label",
            "symbols",
            "selection_count",
            "accent_color",
            "is_active",
        )
        read_only_fields = fields

    def get_symbols(
        self,
        obj: LotteryProduct,
    ) -> list[str]:
        return list(
            obj.symbol_tokens
        )


class EventSerializer(serializers.ModelSerializer):
    """
    Contrato público de DrawEvent.

    Incluye solamente información pública del evento y conserva el contrato
    utilizado por la API existente.
    """

    product = ProductSerializer(
        read_only=True,
    )

    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    price = serializers.SerializerMethodField()
    prize = serializers.SerializerMethodField()
    is_open_now = serializers.SerializerMethodField()

    class Meta:
        model = DrawEvent
        fields = (
            "id",
            "name",
            "product",
            "status",
            "status_label",
            "sales_open_at",
            "sales_close_at",
            "draw_at",
            "price",
            "prize",
            "is_open_now",
        )
        read_only_fields = fields

    def get_price(
        self,
        obj: DrawEvent,
    ) -> dict[str, object]:
        return money_data(
            obj.price_minor,
            currency=Wallet.Currency.VIRTUAL,
        )

    def get_prize(
        self,
        obj: DrawEvent,
    ) -> dict[str, object]:
        return money_data(
            obj.prize_minor,
            currency=Wallet.Currency.VIRTUAL,
        )

    def get_is_open_now(
        self,
        obj: DrawEvent,
    ) -> bool:
        return (
            obj.status
            == DrawEvent.Status.SALES_OPEN
            and timezone.now()
            < obj.sales_close_at
        )


class ResultEventSerializer(serializers.ModelSerializer):
    """
    Resumen del evento incluido dentro de un resultado público.

    No reutilizamos EventSerializer porque un resultado no necesita duplicar
    precio, premio, estado y horarios de venta completos.
    """

    product = ProductSerializer(
        read_only=True,
    )

    class Meta:
        model = DrawEvent
        fields = (
            "id",
            "name",
            "product",
            "draw_at",
        )
        read_only_fields = fields


class ResultSerializer(serializers.ModelSerializer):
    """
    Contrato público de DrawResult.

    No expone usuario administrador, motivo interno ni información privada.
    """

    event = ResultEventSerializer(
        read_only=True,
    )

    winning_symbols = serializers.SerializerMethodField()

    publication_source_label = serializers.CharField(
        source="get_publication_source_display",
        read_only=True,
    )

    class Meta:
        model = DrawResult
        fields = (
            "id",
            "event",
            "winning_key",
            "winning_symbols",
            "publication_source",
            "publication_source_label",
            "published_at",
        )
        read_only_fields = fields

    def get_winning_symbols(
        self,
        obj: DrawResult,
    ) -> list[str]:
        return list(
            obj.key_tokens
        )