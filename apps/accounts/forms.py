"""Formularios server-side del módulo accounts.

Este archivo conserva los formularios ya usados por login, registro y selección
de modo, y añade los formularios específicos del CRUD administrativo de
usuarios y versiones legales.
"""

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm,
)
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
    """Añade una clase CSS sin duplicarla."""
    classes = widget.attrs.get("class", "").split()
    if css_class not in classes:
        classes.append(css_class)
    widget.attrs["class"] = " ".join(classes)


def _apply_bootstrap_widgets(form: forms.Form) -> None:
    """Aplica clases Bootstrap sin convertir el navegador en fuente de verdad."""
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
    """Añade estado Bootstrap y ARIA después de validar en el servidor."""

    def full_clean(self) -> None:
        super().full_clean()
        for field_name in self.errors:
            field = self.fields.get(field_name)
            if field is None:
                continue
            _append_css_class(field.widget, "is-invalid")
            field.widget.attrs["aria-invalid"] = "true"


class UserIdentityValidationMixin:
    """Normalización y unicidad portable para altas y modificaciones."""

    def _other_users(self):
        queryset = User.objects.all()
        instance = getattr(self, "instance", None)
        if instance is not None and instance.pk:
            queryset = queryset.exclude(pk=instance.pk)
        return queryset

    def clean_username(self) -> str:
        username = User.normalize_username_value(
            self.cleaned_data.get("username")
        )
        if not username:
            raise ValidationError("El usuario es obligatorio.")
        if self._other_users().filter(username__iexact=username).exists():
            raise ValidationError("Ya existe una cuenta con este usuario.")
        return username

    def clean_email(self) -> str:
        email = User.normalize_email_value(self.cleaned_data.get("email"))
        if not email:
            raise ValidationError("El correo electrónico es obligatorio.")
        if self._other_users().filter(email__iexact=email).exists():
            raise ValidationError("Ya existe una cuenta con este correo.")
        return email

    def clean_document(self) -> str:
        document = User.normalize_document_value(
            self.cleaned_data.get("document")
        )
        if not document:
            raise ValidationError("El documento es obligatorio.")
        if self._other_users().filter(document__iexact=document).exists():
            raise ValidationError("Ya existe una cuenta con este documento.")
        return document

    def clean_phone(self) -> str:
        return (self.cleaned_data.get("phone") or "").strip()

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get("birth_date")
        if birth_date is None:
            raise ValidationError("La fecha de nacimiento es obligatoria.")
        if birth_date > age_cutoff():
            raise ValidationError("El usuario debe ser mayor de edad.")
        return birth_date

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        is_active = cleaned_data.get("is_active")

        if status == User.Status.ACTIVE and is_active is False:
            self.add_error(
                "is_active",
                "Un usuario con estado Activo debe tener acceso habilitado.",
            )
        elif status and status != User.Status.ACTIVE and is_active is True:
            self.add_error(
                "is_active",
                "Un usuario suspendido, bloqueado o desactivado no puede "
                "mantener acceso habilitado.",
            )
        return cleaned_data

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

    def clean_username(self) -> str:
        return User.normalize_username_value(
            self.cleaned_data.get("username")
        )

    def confirm_login_allowed(self, user) -> None:
        if user.status != User.Status.ACTIVE:
            raise ValidationError(
                "La cuenta no está activa para iniciar operaciones.",
                code="inactive_status",
            )
        super().confirm_login_allowed(user)


class RegistrationForm(
    BootstrapValidationMixin,
    UserIdentityValidationMixin,
    UserCreationForm,
):
    """Registro público de cliente adulto con aceptación legal versionada."""

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
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.terms_version = current_terms_version(TermsVersion.Kind.TERMS)
        self.privacy_version = current_terms_version(
            TermsVersion.Kind.PRIVACY
        )
        self.fields["birth_date"].widget.attrs["max"] = (
            age_cutoff().isoformat()
        )
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["password1"].widget.attrs["autocomplete"] = (
            "new-password"
        )
        self.fields["password2"].widget.attrs["autocomplete"] = (
            "new-password"
        )

        if self.terms_version:
            self.fields["accept_terms"].help_text = (
                f"{self.terms_version.title}, "
                f"versión {self.terms_version.version}."
            )
        if self.privacy_version:
            self.fields["accept_privacy"].help_text = (
                f"{self.privacy_version.title}, "
                f"versión {self.privacy_version.version}."
            )

        _apply_bootstrap_widgets(self)

    def clean(self):
        cleaned_data = super().clean()
        if self.terms_version is None or self.privacy_version is None:
            raise ValidationError(
                "El registro está temporalmente cerrado porque faltan "
                "términos o privacidad vigentes."
            )
        return cleaned_data

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


class UserAdminCreationForm(
    UserIdentityValidationMixin,
    UserCreationForm,
):
    """Alta administrativa segura; UserCreationForm usa set_password()."""

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
            "status",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].widget.attrs["max"] = (
            age_cutoff().isoformat()
        )


class UserAdminChangeForm(
    UserIdentityValidationMixin,
    UserChangeForm,
):
    """Edición administrativa sin exponer ni reemplazar la contraseña."""

    class Meta(UserChangeForm.Meta):
        model = User
        fields = (
            "username",
            "password",
            "email",
            "document",
            "phone",
            "birth_date",
            "first_name",
            "last_name",
            "status",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].widget.attrs["max"] = (
            age_cutoff().isoformat()
        )


class TermsVersionForm(forms.ModelForm):
    """CRUD legal con preservación del contenido que ya fue aceptado."""

    class Meta:
        model = TermsVersion
        fields = (
            "kind",
            "version",
            "title",
            "content",
            "effective_at",
            "is_active",
        )
        widgets = {
            "effective_at": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M:%S",
                attrs={
                    "type": "datetime-local",
                    "step": "1",
                },
            ),
            "content": forms.Textarea(attrs={"rows": 12}),
        }

    def clean_version(self) -> str:
        version = (self.cleaned_data.get("version") or "").strip()
        if not version:
            raise ValidationError("La versión es obligatoria.")
        return version

    def clean_title(self) -> str:
        title = (self.cleaned_data.get("title") or "").strip()
        if not title:
            raise ValidationError("El título es obligatorio.")
        return title

    def clean_content(self) -> str:
        content = (self.cleaned_data.get("content") or "").strip()
        if not content:
            raise ValidationError("El contenido es obligatorio.")
        return content

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["effective_at"].input_formats = (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
        )

    def clean(self):
        cleaned_data = super().clean()

        if not self.instance.pk:
            return cleaned_data

        if not self.instance.acceptances.exists():
            return cleaned_data

        original = (
            TermsVersion.objects
            .filter(pk=self.instance.pk)
            .values(
                "kind",
                "version",
                "title",
                "content",
                "effective_at",
            )
            .first()
        )
        if original is None:
            return cleaned_data

        changed_immutable_fields: set[str] = set()

        for field_name in ("kind", "version", "title", "content"):
            if cleaned_data.get(field_name) != original[field_name]:
                changed_immutable_fields.add(field_name)

        submitted_effective_at = cleaned_data.get("effective_at")
        original_effective_at = original["effective_at"]

        if submitted_effective_at is not None:
            submitted_effective_at = submitted_effective_at.replace(
                microsecond=0
            )
        if original_effective_at is not None:
            original_effective_at = original_effective_at.replace(
                microsecond=0
            )

        if submitted_effective_at != original_effective_at:
            changed_immutable_fields.add("effective_at")

        if changed_immutable_fields:
            changed_labels = ", ".join(
                self.fields[field_name].label
                for field_name in sorted(changed_immutable_fields)
            )
            raise ValidationError(
                "Una versión legal aceptada conserva su contenido histórico. "
                f"No se pueden modificar: {changed_labels}. "
                "Desactiva esta versión y crea una nueva."
            )

        return cleaned_data



class ModeSelectionForm(forms.Form):
    """Valida que el modo enviado pertenezca realmente al usuario."""

    mode = forms.ChoiceField(label="Modo")

    def __init__(
        self,
        *args,
        assigned_modes: tuple[str, ...],
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.fields["mode"].choices = [
            (code, ROLE_PRESENTATION[code]["label"])
            for code in assigned_modes
        ]