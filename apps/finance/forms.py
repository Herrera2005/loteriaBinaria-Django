from __future__ import annotations

import uuid
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError


class MoneyOperationForm(forms.Form):
    amount = forms.DecimalField(
        label="Monto",
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "inputmode": "decimal",
            }
        ),
    )
    operation_id = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial.setdefault("operation_id", uuid.uuid4())

    def amount_minor(self) -> int:
        return int(self.cleaned_data["amount"] * 100)


class TopUpForm(MoneyOperationForm):
    pass


class ConversionForm(MoneyOperationForm):
    pass


class WithdrawalForm(MoneyOperationForm):
    pass


class VirtualTransferForm(MoneyOperationForm):
    recipient = forms.CharField(
        label="Usuario o correo del destinatario",
        max_length=254,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "off",
            }
        ),
    )


class VendorInventoryPurchaseForm(MoneyOperationForm):
    amount = forms.DecimalField(
        label="VIRTUAL a comprar",
        min_value=Decimal("1.00"),
        max_digits=12,
        decimal_places=2,
        help_text=(
            "Ingresa unidades VIRTUAL completas. "
            "Cada V 1.00 cuesta $ 0.90 REAL."
        ),
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "1.00",
                "min": "1.00",
                "inputmode": "decimal",
            }
        ),
    )

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        amount_minor = int(amount * 100)
        if amount_minor % 100 != 0:
            raise ValidationError(
                "La compra mayorista debe usar unidades VIRTUAL completas."
            )
        return amount
