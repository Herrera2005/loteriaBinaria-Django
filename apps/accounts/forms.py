"""Formularios server-side del módulo accounts.

Este archivo conserva los formularios ya usados por login, registro y selección
de modo, y añade los formularios específicos del CRUD administrativo de
usuarios y versiones legales.
"""

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.models import Case, IntegerField, When

from .models import TermsVersion, User
from .roles import ADMINISTRATOR, ROLE_CODES, ROLE_PRESENTATION
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
        if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
            css_class = "form-check-input"
        elif isinstance(widget, forms.Select):
            css_class = "form-select"
        else:
            css_class = "form-control"
        _append_css_class(widget, css_class)


BIRTH_DATE_INPUT_FORMAT = "%Y-%m-%d"


def _birth_date_widget() -> forms.DateInput:
    """Renderiza fechas HTML5 en ISO para evitar campos visualmente vacíos."""
    return forms.DateInput(
        format=BIRTH_DATE_INPUT_FORMAT,
        attrs={"type": "date"},
    )


def _configure_birth_date_field(form: forms.Form) -> None:
    """Alinea renderizado, lectura y mensajes del input date HTML5."""
    field = form.fields["birth_date"]

    field.input_formats = (BIRTH_DATE_INPUT_FORMAT,)
    field.widget.format = BIRTH_DATE_INPUT_FORMAT
    field.widget.input_type = "date"
    field.widget.attrs["max"] = age_cutoff().isoformat()

    field.error_messages["required"] = (
        "La fecha de nacimiento es obligatoria."
    )
    field.error_messages["invalid"] = (
        "Ingresa una fecha de nacimiento válida."
    )

def _canonical_role_queryset():
    """Limita el panel visual a los tres Groups canónicos y su orden."""
    ordering = Case(
        *(
            When(name=role_code, then=position)
            for position, role_code in enumerate(ROLE_CODES)
        ),
        default=len(ROLE_CODES),
        output_field=IntegerField(),
    )
    return Group.objects.filter(name__in=ROLE_CODES).order_by(ordering)


class BusinessRoleFormMixin:
    """Configura el panel visual sin exponer permisos técnicos individuales."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # El panel visual administra roles de negocio, no permisos técnicos
        # individuales ni la condición de superusuario de Django.
        self.fields.pop("user_permissions", None)
        self.fields.pop("is_superuser", None)

        groups = self.fields.get("groups")
        if groups is not None:
            groups.label = "Roles de negocio"
            groups.required = False

            # Primero se asigna el widget y después el queryset.
            # Al establecer el queryset, Django sincroniza sus opciones
            # con el CheckboxSelectMultiple nuevo.
            groups.widget = forms.CheckboxSelectMultiple()
            groups.queryset = _canonical_role_queryset()

            groups.help_text = (
                "Selecciona únicamente CLIENTE, VENDEDOR y/o "
                "ADMINISTRADOR. El modo activo se elige después al iniciar "
                "sesión. El rol VENDEDOR no crea por sí solo el perfil "
                "vendedor."
            )
        is_staff = self.fields.get("is_staff")
        if is_staff is not None:
            is_staff.label = "Acceso administrativo habilitado (staff)"
            is_staff.help_text = (
                "En la implementación actual debe estar marcado junto con "
                "el rol ADMINISTRADOR para usar los CRUD visuales de "
                "Usuarios, Vendedores y Lotería. No convierte la cuenta en "
                "superusuario."
            )

    def clean(self):
        cleaned_data = super().clean()
        groups = cleaned_data.get("groups")
        selected_roles = {group.name for group in groups} if groups else set()

        if (
            ADMINISTRATOR in selected_roles
            and not cleaned_data.get("is_staff")
        ):
            self.add_error(
                "is_staff",
                (
                    "El rol ADMINISTRADOR requiere Acceso administrativo "
                    "habilitado en la implementación actual."
                ),
            )

        return cleaned_data


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
    """Autenticación por nombre de usuario o correo electrónico."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Usuario o correo electrónico"
        self.fields["password"].label = "Contraseña"
        self.fields["username"].widget.attrs.update(
            {
                "autocomplete": "username",
                "autofocus": True,
                "placeholder": "usuario o correo@ejemplo.com",
            }
        )
        self.fields["password"].widget.attrs.update(
            {"autocomplete": "current-password"}
        )
        _apply_bootstrap_widgets(self)

    def clean(self):
        identifier = User.normalize_username_value(
            self.cleaned_data.get("username")
        )

        if identifier and "@" in identifier:
            matched_username = (
                User.objects
                .filter(email__iexact=identifier)
                .values_list("username", flat=True)
                .first()
            )
            if matched_username:
                self.cleaned_data["username"] = matched_username
            else:
                self.cleaned_data["username"] = identifier
        else:
            self.cleaned_data["username"] = identifier

        return super().clean()

    def confirm_login_allowed(self, user) -> None:
        if user.status != User.Status.ACTIVE:
            raise ValidationError(
                "La cuenta no está activa para iniciar operaciones.",
                code="inactive_status",
            )
        super().confirm_login_allowed(user)


class TallerPasswordChangeForm(
    BootstrapValidationMixin,
    PasswordChangeForm,
):
    """Cambio de contraseña autenticado con estilos Bootstrap."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "Contraseña actual"
        self.fields["new_password1"].label = "Nueva contraseña"
        self.fields["new_password2"].label = "Confirmar nueva contraseña"
        self.fields["old_password"].widget.attrs["autocomplete"] = (
            "current-password"
        )
        self.fields["new_password1"].widget.attrs["autocomplete"] = (
            "new-password"
        )
        self.fields["new_password2"].widget.attrs["autocomplete"] = (
            "new-password"
        )
        _apply_bootstrap_widgets(self)


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
            "birth_date": _birth_date_widget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.terms_version = current_terms_version(TermsVersion.Kind.TERMS)
        self.privacy_version = current_terms_version(
            TermsVersion.Kind.PRIVACY
        )
        _configure_birth_date_field(self)
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
            "birth_date": _birth_date_widget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _configure_birth_date_field(self)


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
            "birth_date": _birth_date_widget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _configure_birth_date_field(self)


class UserBusinessCreationForm(
    BusinessRoleFormMixin,
    UserAdminCreationForm,
):
    """Alta desde el panel visual con roles canónicos y sin permisos directos."""


class UserBusinessChangeForm(
    BusinessRoleFormMixin,
    UserAdminChangeForm,
):
    """Edición visual sin permisos individuales ni superusuario."""


class ProfileUpdateForm(
    BootstrapValidationMixin,
    UserIdentityValidationMixin,
    forms.ModelForm,
):
    """Edición del perfil propio sin exponer privilegios ni contraseña."""

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "document",
            "phone",
            "birth_date",
            "first_name",
            "last_name",
        )
        widgets = {
            "birth_date": _birth_date_widget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _configure_birth_date_field(self)
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["phone"].widget.attrs["autocomplete"] = "tel"
        self.fields["first_name"].widget.attrs["autocomplete"] = "given-name"
        self.fields["last_name"].widget.attrs["autocomplete"] = "family-name"
        _apply_bootstrap_widgets(self)


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