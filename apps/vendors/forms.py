"""Formularios del CRUD evaluable de perfiles vendedores."""

from __future__ import annotations

from django import forms
import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q

from apps.accounts.roles import VENDOR

from .models import (
    ACTIVE_USER_STATUS,
    VendorProfile,
    validate_vendor_account,
)


User = get_user_model()


def _append_css_class(widget: forms.Widget, css_class: str) -> None:
    classes = widget.attrs.get("class", "").split()
    if css_class not in classes:
        classes.append(css_class)
    widget.attrs["class"] = " ".join(classes)


def _apply_bootstrap_widgets(form: forms.Form) -> None:
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            css_class = "form-check-input"
        elif isinstance(widget, forms.Select):
            css_class = "form-select"
        else:
            css_class = "form-control"
        _append_css_class(widget, css_class)


class VendorProfileForm(forms.ModelForm):
    """Crea y edita perfiles sin exponer solicitudes ni transiciones."""

    class Meta:
        model = VendorProfile
        fields = (
            "user",
            "status",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        eligible_users = User.objects.filter(
            is_active=True,
            status=ACTIVE_USER_STATUS,
            groups__name=VENDOR,
        ).distinct()

        if self.instance.pk:
            eligible_users = User.objects.filter(
                Q(pk=self.instance.user_id)
                | Q(
                    is_active=True,
                    status=ACTIVE_USER_STATUS,
                    groups__name=VENDOR,
                )
            ).distinct()
            self.fields["user"].disabled = True
            self.fields["user"].help_text = (
                "El usuario del perfil no se cambia después de crearlo."
            )
        else:
            eligible_users = eligible_users.filter(vendor_profile__isnull=True)
            self.fields["user"].help_text = (
                "Solo aparecen cuentas activas con el rol VENDEDOR y sin perfil."
            )

        self.fields["user"].queryset = eligible_users.order_by("username")
        _apply_bootstrap_widgets(self)

    def clean_user(self):
        user = self.cleaned_data["user"]
        is_current_user = (
            bool(self.instance.pk)
            and user.pk == self.instance.user_id
        )

        if not is_current_user:
            try:
                validate_vendor_account(user, require_active=True)
            except ValidationError as exc:
                messages = [
                    message
                    for field_messages in exc.message_dict.values()
                    for message in field_messages
                ]
                raise ValidationError(" ".join(messages)) from exc

        duplicate = VendorProfile.objects.filter(user=user)
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise ValidationError(
                "Este usuario ya tiene un perfil de vendedor."
            )

        return user

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        status = cleaned_data.get("status")

        if user is not None and status == VendorProfile.Status.ACTIVE:
            try:
                validate_vendor_account(user, require_active=True)
            except ValidationError as exc:
                for field_name, messages in exc.message_dict.items():
                    target_field = field_name if field_name in self.fields else "status"
                    for message in messages:
                        self.add_error(target_field, message)

        return cleaned_data


class ConversionRequestCreateForm(forms.Form):
    """Captura un monto REAL sin usar float y una clave idempotente."""

    amount = forms.DecimalField(
        label="Monto REAL a convertir",
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
        help_text=(
            "El monto se reservará en tu wallet REAL hasta que la "
            "solicitud se complete, cancele o expire."
        ),
    )
    operation_id = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial.setdefault("operation_id", uuid.uuid4())

    def amount_minor(self) -> int:
        return int(self.cleaned_data["amount"] * 100)
