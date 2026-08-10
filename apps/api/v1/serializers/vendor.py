from __future__ import annotations

from rest_framework import serializers

from apps.finance.models import (
    Movement,
    VendorInventoryPurchase,
    Wallet,
)
from apps.vendors.models import (
    ConversionAssignment,
    ConversionRequest,
    VendorProfile,
)


def _money_data(amount_minor: int) -> dict[str, object]:
    amount_minor = int(amount_minor)

    return {
        "minor": amount_minor,
        "display": f"V {amount_minor / 100:,.2f}",
    }


class VendorProfileSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = VendorProfile
        fields = (
            "id",
            "status",
            "status_label",
            "activated_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class VendorWalletSerializer(serializers.ModelSerializer):
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

    def get_available(self, obj):
        return _money_data(
            obj.available_minor
        )

    def get_reserved(self, obj):
        return _money_data(
            obj.reserved_minor
        )

    def get_total(self, obj):
        return _money_data(
            obj.available_minor
            + obj.reserved_minor
        )


class VendorMovementWalletSerializer(
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


class VendorMovementSerializer(
    serializers.ModelSerializer
):
    wallet = VendorMovementWalletSerializer(
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

    def get_amount(self, obj):
        return _money_data(
            obj.amount_minor
        )

    def get_balance_after(self, obj):
        return _money_data(
            obj.balance_after_minor
        )


class VendorConversionRequestSerializer(
    serializers.ModelSerializer
):
    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    amount = serializers.SerializerMethodField()

    class Meta:
        model = ConversionRequest
        fields = (
            "id",
            "amount",
            "status",
            "status_label",
            "expires_at",
            "created_at",
        )
        read_only_fields = fields

    def get_amount(self, obj):
        return _money_data(
            obj.amount_minor
        )


class VendorAssignmentRequestSerializer(
    serializers.ModelSerializer
):
    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    amount = serializers.SerializerMethodField()

    class Meta:
        model = ConversionRequest
        fields = (
            "id",
            "amount",
            "status",
            "status_label",
            "expires_at",
            "completed_at",
            "created_at",
        )
        read_only_fields = fields

    def get_amount(self, obj):
        return _money_data(
            obj.amount_minor
        )


class VendorAssignmentSerializer(
    serializers.ModelSerializer
):
    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    request = VendorAssignmentRequestSerializer(
        read_only=True,
    )

    class Meta:
        model = ConversionAssignment
        fields = (
            "id",
            "request",
            "status",
            "status_label",
            "assigned_at",
            "released_at",
            "completed_at",
        )
        read_only_fields = fields

class VendorInventoryPurchaseSerializer(
    serializers.ModelSerializer
):
    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    virtual = serializers.SerializerMethodField()
    real_cost = serializers.SerializerMethodField()

    class Meta:
        model = VendorInventoryPurchase
        fields = (
            "id",
            "status",
            "status_label",
            "virtual",
            "real_cost",
            "created_at",
        )
        read_only_fields = fields

    def get_virtual(self, obj):
        return _money_data(
            obj.amount_minor
        )

    def get_real_cost(self, obj):
        return _money_data(
            obj.cost_real_minor
        )


class VendorInventoryPurchaseInputSerializer(
    serializers.Serializer
):
    virtual_minor = serializers.IntegerField(
        min_value=1,
    )