from __future__ import annotations

from rest_framework import serializers

from apps.finance.models import (
    Movement,
    Wallet,
)
from apps.lottery.models import Ticket


def _money_data(amount_minor: int) -> dict[str, object]:
    amount_minor = int(amount_minor)

    return {
        "minor": amount_minor,
        "display": f"V {amount_minor / 100:,.2f}",
    }


class ClientWalletSerializer(serializers.ModelSerializer):
    currency_label = serializers.CharField(
        source="get_currency_display",
        read_only=True,
    )

    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    available = serializers.SerializerMethodField()
    reserved = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = (
            "id",
            "currency",
            "currency_label",
            "status",
            "status_label",
            "available",
            "reserved",
            "total",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_available(
        self,
        obj: Wallet,
    ) -> dict[str, object]:
        return _money_data(
            obj.available_minor
        )

    def get_reserved(
        self,
        obj: Wallet,
    ) -> dict[str, object]:
        return _money_data(
            obj.reserved_minor
        )

    def get_total(
        self,
        obj: Wallet,
    ) -> dict[str, object]:
        return _money_data(
            obj.available_minor
            + obj.reserved_minor
        )


class ClientTicketProductSerializer(
    serializers.Serializer
):
    id = serializers.IntegerField(
        read_only=True,
    )
    code = serializers.CharField(
        read_only=True,
    )
    name = serializers.CharField(
        read_only=True,
    )
    accent_color = serializers.CharField(
        read_only=True,
    )


class ClientTicketEventSerializer(
    serializers.Serializer
):
    id = serializers.IntegerField(
        read_only=True,
    )
    name = serializers.CharField(
        read_only=True,
    )
    status = serializers.CharField(
        read_only=True,
    )
    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    draw_at = serializers.DateTimeField(
        read_only=True,
    )
    product = ClientTicketProductSerializer(
        read_only=True,
    )


class ClientTicketSerializer(
    serializers.ModelSerializer
):
    event = ClientTicketEventSerializer(
        read_only=True,
    )

    combination = serializers.SerializerMethodField()

    price = serializers.SerializerMethodField()

    ownership_status_label = serializers.CharField(
        source="get_ownership_status_display",
        read_only=True,
    )

    evaluation_status_label = serializers.CharField(
        source="get_evaluation_status_display",
        read_only=True,
    )

    award = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = (
            "id",
            "event",
            "combination",
            "price",
            "ownership_status",
            "ownership_status_label",
            "evaluation_status",
            "evaluation_status_label",
            "award",
            "credited_at",
            "created_at",
        )
        read_only_fields = fields

    def get_combination(
        self,
        obj: Ticket,
    ) -> dict[str, object]:
        return {
            "key": obj.normalized_key,
            "display": obj.key_display,
            "symbols": list(
                obj.key_tokens
            ),
        }

    def get_price(
        self,
        obj: Ticket,
    ) -> dict[str, object]:
        return _money_data(
            obj.price_minor
        )

    def get_award(
        self,
        obj: Ticket,
    ) -> dict[str, object]:
        return _money_data(
            obj.award_minor
        )


class ClientTicketPurchaseSerializer(
    serializers.Serializer
):
    """
    Entrada HTTP para comprar un boleto.

    La validación real de combinación, evento, saldo y disponibilidad
    continúa perteneciendo al servicio de dominio purchase_ticket().
    """

    event_id = serializers.IntegerField(
        min_value=1,
    )

    symbols = serializers.ListField(
        child=serializers.CharField(
            allow_blank=False,
            trim_whitespace=True,
            max_length=32,
        ),
        allow_empty=False,
        min_length=1,
        max_length=8,
    )

    def validate_symbols(self, value):
        return [
            symbol.strip()
            for symbol in value
        ]

class ClientMovementWalletSerializer(
    serializers.Serializer
):
    id = serializers.IntegerField(
        read_only=True,
    )
    currency = serializers.CharField(
        read_only=True,
    )
    currency_label = serializers.CharField(
        source="get_currency_display",
        read_only=True,
    )


class ClientMovementSerializer(
    serializers.ModelSerializer
):
    wallet = ClientMovementWalletSerializer(
        read_only=True,
    )

    type_label = serializers.CharField(
        source="get_type_display",
        read_only=True,
    )

    direction_label = serializers.CharField(
        source="get_direction_display",
        read_only=True,
    )

    amount = serializers.SerializerMethodField()
    balance_after = serializers.SerializerMethodField()

    class Meta:
        model = Movement
        fields = (
            "id",
            "wallet",
            "type",
            "type_label",
            "direction",
            "direction_label",
            "amount",
            "balance_after",
            "description",
            "created_at",
        )
        read_only_fields = fields

    def get_amount(
        self,
        obj: Movement,
    ) -> dict[str, object]:
        return _money_data(
            obj.amount_minor
        )

    def get_balance_after(
        self,
        obj: Movement,
    ) -> dict[str, object]:
        return _money_data(
            obj.balance_after_minor
        )