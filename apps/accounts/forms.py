"""Formularios server-side de autenticación, registro y modo."""

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import TermsVersion, User
from .roles import ROLE_PRESENTATION
from .services import (
    RegistrationData,
    age_cutoff,
    current_terms_version,
    register_client,
)


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


class BootstrapValidationMixin:
    """Añade estado Bootstrap/ARIA después de la validación server-side."""

    def full_clean(self):
        super().full_clean()
        for field_name in self.errors:
            field = self.fields.get(field_name)
            if field is None:
                continue
            _append_css_class(field.widget, "is-invalid")
            field.widget.attrs["aria-invalid"] = "true"


class TallerAuthenticationForm(BootstrapValidationMixin, AuthenticationForm):
    """Login con widgets Bootstrap y bloqueo por estado académico."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Usuario"
        self.fields["password"].label = "Contraseña"
        self.fields["username"].widget.attrs.update(
            {"autocomplete": "username", "autofocus": True}
        )
        self.fields["password"].widget.attrs.update(
            {"autocomplete": "current-password"}
        )
        _apply_bootstrap_widgets(self)

    def clean_username(self):
        return User.normalize_username_value(
            self.cleaned_data.get("username")
        )

    def confirm_login_allowed(self, user):
        if user.status != User.Status.ACTIVE:
            raise ValidationError(
                "La cuenta no está activa para iniciar operaciones.",
                code="inactive_status",
            )
        super().confirm_login_allowed(user)


class RegistrationForm(BootstrapValidationMixin, UserCreationForm):
    """Registro de cliente adulto con aceptación versionada."""

    accept_terms = forms.BooleanField(
        label="Acepto los términos académicos vigentes",
        required=True,
    )
    accept_privacy = forms.BooleanField(
        label="Acepto la política académica de privacidad vigente",
        required=True,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "document",
            "phone",
            "birth_date",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "accept_terms",
            "accept_privacy",
        )
        widgets = {"birth_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.terms_version = current_terms_version(TermsVersion.Kind.TERMS)
        self.privacy_version = current_terms_version(TermsVersion.Kind.PRIVACY)
        self.fields["birth_date"].widget.attrs["max"] = age_cutoff().isoformat()
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"
        if self.terms_version:
            self.fields["accept_terms"].help_text = (
                f"{self.terms_version.title}, versión {self.terms_version.version}."
            )
        if self.privacy_version:
            self.fields["accept_privacy"].help_text = (
                f"{self.privacy_version.title}, versión {self.privacy_version.version}."
            )
        _apply_bootstrap_widgets(self)

    def clean_username(self):
        username = User.normalize_username_value(
            self.cleaned_data.get("username")
        )
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Ya existe una cuenta con este usuario.")
        return username

    def clean_email(self):
        email = User.normalize_email_value(self.cleaned_data.get("email"))
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe una cuenta con este correo.")
        return email

    def clean_document(self):
        document = User.normalize_document_value(
            self.cleaned_data.get("document")
        )
        if User.objects.filter(document__iexact=document).exists():
            raise ValidationError("Ya existe una cuenta con este documento.")
        return document

    def clean_birth_date(self):
        birth_date = self.cleaned_data["birth_date"]
        if birth_date > age_cutoff():
            raise ValidationError("Debes ser mayor de edad para registrarte.")
        return birth_date

    def clean(self):
        cleaned = super().clean()
        if self.terms_version is None or self.privacy_version is None:
            raise ValidationError(
                "El registro está temporalmente cerrado porque faltan "
                "términos o privacidad vigentes."
            )
        return cleaned

    def save(self, *, ip_address: str | None = None):
        if self.errors:
            raise ValueError("No se puede guardar un formulario inválido.")
        data = RegistrationData(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            document=self.cleaned_data["document"],
            phone=self.cleaned_data.get("phone", ""),
            birth_date=self.cleaned_data["birth_date"],
            first_name=self.cleaned_data.get("first_name", ""),
            last_name=self.cleaned_data.get("last_name", ""),
            password=self.cleaned_data["password1"],
        )
        return register_client(
            data=data,
            terms_version=self.terms_version,
            privacy_version=self.privacy_version,
            ip_address=ip_address,
        )


class ModeSelectionForm(forms.Form):
    """Valida que el modo enviado pertenezca realmente al usuario."""

    mode = forms.ChoiceField(label="Modo")

    def __init__(self, *args, assigned_modes: tuple[str, ...], **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["mode"].choices = [
            (code, ROLE_PRESENTATION[code]["label"])
            for code in assigned_modes
        ]
