"""Formularios del CRUD evaluable de productos y eventos."""

from __future__ import annotations

from django import forms
from django.utils import timezone

from .models import (
    MAX_PRODUCT_SYMBOLS,
    MAX_SYMBOL_TOKEN_LENGTH,
    DrawEvent,
    DrawEventSeries,
    LotteryProduct,
    validate_key_for_product,
)
import uuid
from decimal import Decimal

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


class LotteryProductForm(forms.ModelForm):
    """Crea productos oficiales o personalizados con símbolos tokenizados."""

    class ProductType:
        OCTAL = LotteryProduct.Code.OCTAL
        DECIMAL = LotteryProduct.Code.DECIMAL
        HEXADECIMAL = LotteryProduct.Code.HEXADECIMAL
        CUSTOM = LotteryProduct.Kind.CUSTOM
        choices = (
            (OCTAL, "Octal oficial"),
            (DECIMAL, "Decimal oficial"),
            (HEXADECIMAL, "Hexadecimal oficial"),
            (CUSTOM, "Personalizado"),
        )

    class SymbolMode:
        MANUAL = "MANUAL"
        NUMERIC_RANGE = "NUMERIC_RANGE"
        LETTER_RANGE = "LETTER_RANGE"
        choices = (
            (MANUAL, "Agregar símbolos por casillas"),
            (NUMERIC_RANGE, "Rango numérico"),
            (LETTER_RANGE, "Rango de letras"),
        )

    product_type = forms.ChoiceField(
        label="Tipo de producto",
        choices=ProductType.choices,
        required=False,
    )
    symbol_mode = forms.ChoiceField(
        label="Cómo definir los símbolos",
        choices=SymbolMode.choices,
        required=False,
        initial=SymbolMode.MANUAL,
    )
    range_start = forms.CharField(
        label="Desde",
        max_length=2,
        required=False,
    )
    range_end = forms.CharField(
        label="Hasta",
        max_length=2,
        required=False,
    )

    accent_color = forms.CharField(
        label="Color identificador",
        required=False,
        initial="#FD7E14",
        max_length=7,
        widget=forms.TextInput(
            attrs={
                "type": "color",
                "class": "form-control form-control-color",
                "title": "Selecciona un color identificador",
                "aria-label": "Color identificador del producto",
            }
        ),
        help_text=(
            "Se usa en bordes y símbolos. "
            "Si no selecciona uno, se aplicará el color predeterminado."
        ),
    )

    class Meta:
        model = LotteryProduct
        fields = (
            "code",
            "name",
            "allowed_symbols",
            "selection_count",
            "accent_color",
            "is_active",
        )
        widgets = {
            "code": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "spellcheck": "false",
                    "class": "text-uppercase",
                }
            ),
            "allowed_symbols": forms.HiddenInput(),
            "selection_count": forms.NumberInput(
                attrs={"min": 2, "max": 8}
            ),
            "accent_color": forms.TextInput(
                attrs={
                    "type": "color",
                    "class": "form-control form-control-color",
                    "title": "Seleccione el color identificador del producto",
                }
            ),
        }

    field_order = (
        "product_type",
        "code",
        "name",
        "symbol_mode",
        "range_start",
        "range_end",
        "allowed_symbols",
        "selection_count",
        "accent_color",
        "is_active",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _apply_bootstrap_widgets(self)

        accent_field = self.fields["accent_color"]

        accent_field.required = False
        accent_field.initial = "#FD7E14"

        accent_field.widget = forms.TextInput(
            attrs={
                "type": "color",
                "class": "form-control form-control-color",
                "title": "Selecciona un color identificador",
                "aria-label": "Color identificador del producto",
            }
        )

        current_color = getattr(
            self.instance,
            "accent_color",
            "",
        )

        if not self.is_bound:
            self.initial["accent_color"] = (
                current_color or "#FD7E14"
            )

        self.fields["code"].required = False
        self.fields["allowed_symbols"].required = False
        self.fields["selection_count"].required = False

        self.fields["code"].help_text = (
            "Para personalizados use letras, números y guion bajo; se "
            "guardará en mayúsculas."
        )
        self.fields["selection_count"].help_text = (
            "Entre 2 y 8; no puede superar el universo de símbolos."
        )
        self.fields["accent_color"].help_text = (
            "Identifica visualmente este producto. El nombre y código siempre "
            "se muestran; el color no es la única señal."
        )
        self.fields["range_start"].widget.attrs.update(
            {
                "class": "form-control text-uppercase",
                "autocomplete": "off",
                "inputmode": "text",
            }
        )
        self.fields["range_end"].widget.attrs.update(
            {
                "class": "form-control text-uppercase",
                "autocomplete": "off",
                "inputmode": "text",
            }
        )

        self._original_kind = self.instance.kind if self.instance.pk else None
        if self.instance.pk:
            if self.instance.kind == LotteryProduct.Kind.OFFICIAL:
                self.initial["product_type"] = self.instance.code
            else:
                self.initial["product_type"] = self.ProductType.CUSTOM
            self.initial["symbol_mode"] = self.SymbolMode.MANUAL

        self._immutable_product = bool(
            self.instance.pk and self.instance.events.exists()
        )
        self.symbols_disabled = self._immutable_product
        if self._immutable_product:
            for field_name in (
                "product_type",
                "code",
                "symbol_mode",
                "range_start",
                "range_end",
                "allowed_symbols",
                "selection_count",
            ):
                self.fields[field_name].disabled = True
            self.fields["code"].help_text = (
                "La configuración no cambia cuando ya existen eventos."
            )

        self.symbol_token_values = self._initial_symbol_token_values()

    def _posted_symbol_tokens(self) -> list[str]:
        if not self.is_bound:
            return []

        if hasattr(self.data, "getlist"):
            values = self.data.getlist("symbol_token")
        else:
            value = self.data.get("symbol_token", [])
            values = value if isinstance(value, (list, tuple)) else [value]

        return [str(value or "").strip().upper() for value in values]

    def _initial_symbol_token_values(self) -> list[str]:
        posted = self._posted_symbol_tokens()
        if posted:
            return posted

        if self.instance.pk and self.instance.kind == LotteryProduct.Kind.CUSTOM:
            return list(self.instance.symbol_tokens)

        legacy_value = ""
        if self.is_bound:
            legacy_value = str(self.data.get("allowed_symbols", "") or "")
        if legacy_value:
            return list(LotteryProduct.parse_symbol_storage(legacy_value))

        return ["", ""]

    @staticmethod
    def _validate_generated_size(tokens: list[str]) -> list[str]:
        if len(tokens) > MAX_PRODUCT_SYMBOLS:
            raise forms.ValidationError(
                f"El rango genera más de {MAX_PRODUCT_SYMBOLS} símbolos."
            )
        return tokens

    @classmethod
    def _numeric_range(cls, start: str, end: str) -> list[str]:
        if not start.isdigit() or not end.isdigit():
            raise forms.ValidationError(
                "El rango numérico debe usar números enteros entre 0 y 99."
            )
        start_value = int(start)
        end_value = int(end)
        if not 0 <= start_value <= 99 or not 0 <= end_value <= 99:
            raise forms.ValidationError(
                "El rango numérico debe estar entre 0 y 99."
            )
        if start_value > end_value:
            raise forms.ValidationError(
                "En el rango numérico, Desde no puede ser mayor que Hasta."
            )
        return cls._validate_generated_size(
            [str(value) for value in range(start_value, end_value + 1)]
        )

    @classmethod
    def _letter_range(cls, start: str, end: str) -> list[str]:
        if not (
            len(start) == 1
            and len(end) == 1
            and start.isalpha()
            and end.isalpha()
            and start.isascii()
            and end.isascii()
        ):
            raise forms.ValidationError(
                "El rango de letras debe usar una letra de A a Z en cada límite."
            )
        start = start.upper()
        end = end.upper()
        if ord(start) > ord(end):
            raise forms.ValidationError(
                "En el rango de letras, Desde no puede ser mayor que Hasta."
            )
        return cls._validate_generated_size(
            [chr(value) for value in range(ord(start), ord(end) + 1)]
        )

    def _clean_manual_tokens(self) -> list[str]:
        tokens = [token for token in self._posted_symbol_tokens() if token]
        if not tokens:
            legacy_value = str(self.data.get("allowed_symbols", "") or "")
            tokens = list(LotteryProduct.parse_symbol_storage(legacy_value))

        if len(tokens) < 2:
            self.add_error(
                "allowed_symbols",
                "Agregue al menos dos símbolos en casillas separadas.",
            )

        invalid = [
            token
            for token in tokens
            if not token.isalnum() or len(token) > MAX_SYMBOL_TOKEN_LENGTH
        ]
        if invalid:
            self.add_error(
                "allowed_symbols",
                "Cada casilla admite uno o dos caracteres alfanuméricos.",
            )

        if len(tokens) > MAX_PRODUCT_SYMBOLS:
            self.add_error(
                "allowed_symbols",
                f"El universo admite como máximo {MAX_PRODUCT_SYMBOLS} símbolos.",
            )

        if len(set(tokens)) != len(tokens):
            self.add_error(
                "allowed_symbols",
                "Los símbolos permitidos no pueden repetirse.",
            )

        return tokens

    def clean_accent_color(self):
        field_name = self.add_prefix("accent_color")

        # Compatibilidad con formularios antiguos:
        # si el POST no contiene el campo, conserva el valor existente.
        if (
            self.is_bound
            and field_name not in self.data
            and self.instance.pk
        ):
            existing_color = (
                self.instance.accent_color
                or "#FD7E14"
            )
            return existing_color.strip().upper()

        color = (
            self.cleaned_data.get("accent_color")
            or getattr(self.instance, "accent_color", "")
            or "#FD7E14"
        )

        color = color.strip().upper()
        LotteryProduct.COLOR_VALIDATOR(color)

        return color

    def clean(self):
        cleaned_data = super().clean()

        if self._immutable_product:
            cleaned_data["code"] = self.instance.code
            cleaned_data["allowed_symbols"] = self.instance.allowed_symbols
            cleaned_data["selection_count"] = self.instance.selection_count
            self.instance.kind = self._original_kind
            return cleaned_data

        product_type = cleaned_data.get("product_type")
        explicit_product_type = bool(self.data.get("product_type"))
        if not product_type:
            submitted_code = (cleaned_data.get("code") or "").strip().upper()
            product_type = (
                submitted_code
                if submitted_code in LotteryProduct.PRODUCT_RULES
                else self.ProductType.CUSTOM
            )
            cleaned_data["product_type"] = product_type

        if product_type in LotteryProduct.PRODUCT_RULES:
            self.instance.kind = LotteryProduct.Kind.OFFICIAL
            cleaned_data["code"] = product_type
            if explicit_product_type:
                rule = LotteryProduct.PRODUCT_RULES[product_type]
                cleaned_data["allowed_symbols"] = rule["allowed_symbols"]
                cleaned_data["selection_count"] = rule["selection_count"]
            return cleaned_data

        self.instance.kind = LotteryProduct.Kind.CUSTOM
        code = (cleaned_data.get("code") or "").strip().upper()
        cleaned_data["code"] = code
        if not code:
            self.add_error("code", "Ingrese un código para el producto personalizado.")

        selection_count = cleaned_data.get("selection_count")
        if selection_count is None:
            self.add_error(
                "selection_count",
                "Ingrese la cantidad de posiciones.",
            )

        symbol_mode = cleaned_data.get("symbol_mode") or self.SymbolMode.MANUAL
        range_start = (cleaned_data.get("range_start") or "").strip().upper()
        range_end = (cleaned_data.get("range_end") or "").strip().upper()

        try:
            if symbol_mode == self.SymbolMode.NUMERIC_RANGE:
                tokens = self._numeric_range(range_start, range_end)
            elif symbol_mode == self.SymbolMode.LETTER_RANGE:
                tokens = self._letter_range(range_start, range_end)
            else:
                tokens = self._clean_manual_tokens()
        except forms.ValidationError as exc:
            self.add_error("range_end", exc)
            tokens = []

        cleaned_data["allowed_symbols"] = (
            LotteryProduct.serialize_symbol_tokens(tokens) if tokens else ""
        )
        self.symbol_token_values = tokens or self.symbol_token_values
        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        product.kind = self.instance.kind
        product.code = self.cleaned_data["code"]
        product.allowed_symbols = self.cleaned_data["allowed_symbols"]
        product.selection_count = self.cleaned_data["selection_count"]

        if commit:
            product.full_clean()
            product.save()
            self.save_m2m()
        return product


class DrawEventForm(forms.ModelForm):
    """Edita datos del evento sin exponer transiciones de estado libres."""

    price_minor = forms.DecimalField(
        label="Precio del boleto (VIRTUAL)",
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "inputmode": "decimal",
                "placeholder": "0.00",
            }
        ),
        help_text="Ingrese el valor en dólares, por ejemplo: 1.50.",
    )

    prize_minor = forms.DecimalField(
        label="Premio fijo (VIRTUAL)",
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "inputmode": "decimal",
                "placeholder": "0.00",
            }
        ),
        help_text="Ingrese el premio en dólares, por ejemplo: 50.00.",
    )

    PROTECTED_AFTER_DRAFT = (
        "product",
        "sales_open_at",
        "draw_at",
        "price_minor",
        "prize_minor",
    )

    class Meta:
        model = DrawEvent
        fields = (
            "product",
            "name",
            "sales_open_at",
            "draw_at",
            "price_minor",
            "prize_minor",
        )
        widgets = {
            "sales_open_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "draw_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap_widgets(self)
        self.fields["sales_open_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["draw_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["draw_at"].help_text = (
            "El cierre se calculará automáticamente diez minutos antes."
        )
        self._protected_original_values = {}

        if self.instance.pk:
            self.initial["price_minor"] = (
                Decimal(self.instance.price_minor) / Decimal("100")
            )
            self.initial["prize_minor"] = (
                Decimal(self.instance.prize_minor) / Decimal("100")
            )
            
        if self.instance.pk and self.instance.status != DrawEvent.Status.DRAFT:
            for field_name in self.PROTECTED_AFTER_DRAFT:
                self._protected_original_values[field_name] = getattr(
                    self.instance,
                    field_name,
                )
                self.fields[field_name].disabled = True
            self.fields["name"].help_text = (
                "Solo el nombre descriptivo permanece editable; las condiciones "
                "críticas quedan bloqueadas después de Borrador."
            )

    def clean(self):
        cleaned_data = super().clean()

        if self._protected_original_values:
            for field_name, original_value in self._protected_original_values.items():
                cleaned_data[field_name] = original_value
                setattr(self.instance, field_name, original_value)

        sales_open_at = cleaned_data.get("sales_open_at")
        draw_at = cleaned_data.get("draw_at")
        if draw_at is not None:
            self.instance.sales_close_at = DrawEvent.calculate_sales_close_at(draw_at)
            if sales_open_at is not None and sales_open_at >= self.instance.sales_close_at:
                self.add_error(
                    "sales_open_at",
                    "La apertura debe ser anterior al cierre, que ocurre diez minutos antes del sorteo.",
                )
        return cleaned_data

    def save(self, commit=True):
        event = super().save(commit=False)

        for field_name, original_value in self._protected_original_values.items():
            setattr(event, field_name, original_value)

        def to_minor(field_name):
            value = self.cleaned_data[field_name]
            return int(value * Decimal("100"))

        if "price_minor" not in self._protected_original_values:
            event.price_minor = to_minor("price_minor")
        if "prize_minor" not in self._protected_original_values:
            event.prize_minor = to_minor("prize_minor")

        event.sales_close_at = DrawEvent.calculate_sales_close_at(event.draw_at)
        if not event.pk:
            event.status = DrawEvent.Status.DRAFT
            event.cancellation_reason = ""

        if commit:
            event.full_clean()
            event.save()
            self.save_m2m()
        return event


class DrawEventTransitionForm(forms.Form):
    reason = forms.CharField(
        label="Motivo administrativo",
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    public_message = forms.CharField(
        label="Mensaje visible para clientes",
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Se mostrará en el detalle público del sorteo.",
    )

    def __init__(self, *args, require_public_message=False, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap_widgets(self)
        if require_public_message:
            self.fields["public_message"].required = True


class TicketPurchaseForm(forms.Form):
    """Compra o consulta parcial mediante una casilla por posición."""

    combination = forms.CharField(required=False, widget=forms.HiddenInput())
    operation_id = forms.UUIDField(widget=forms.HiddenInput())

    def __init__(self, *args, event, require_complete=True, **kwargs):
        self.event = event
        self.require_complete = require_complete
        self.selected_tokens = ()
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial.setdefault("operation_id", uuid.uuid4())

        choices = (("", "—"),) + tuple(
            (token, token) for token in event.product.symbol_tokens
        )
        self.position_field_names = []
        for index in range(1, event.product.selection_count + 1):
            field_name = f"position_{index}"
            self.position_field_names.append(field_name)
            self.fields[field_name] = forms.ChoiceField(
                label=f"Posición {index}",
                choices=choices,
                required=False,
                error_messages={
                    "invalid_choice": "El símbolo seleccionado no está permitido.",
                },
                widget=forms.Select(
                    attrs={
                        "class": "form-select font-monospace text-center",
                        "aria-label": f"Símbolo para la posición {index}",
                        "data-ticket-position": str(index),
                    }
                ),
            )

    @property
    def position_fields(self):
        return [self[field_name] for field_name in self.position_field_names]

    def clean(self):
        cleaned_data = super().clean()
        has_position_payload = any(
            field_name in self.data for field_name in self.position_field_names
        )

        if has_position_payload:
            tokens = []
            for field_name in self.position_field_names:
                token = cleaned_data.get(field_name) or ""
                if self.require_complete and not token and field_name not in self.errors:
                    self.add_error(field_name, "Seleccione un símbolo.")
                tokens.append(token)

            non_empty = tuple(token for token in tokens if token)
            seen = set()
            for field_name, token in zip(self.position_field_names, tokens):
                if token and token in seen and field_name not in self.errors:
                    self.add_error(
                        field_name,
                        "Este símbolo ya fue seleccionado en otra posición.",
                    )
                seen.add(token)

            if any(field_name in self.errors for field_name in self.position_field_names):
                return cleaned_data

            self.selected_tokens = non_empty
            if not self.require_complete:
                if not non_empty:
                    self.add_error(None, "Seleccione al menos un símbolo para consultar disponibilidad.")
                return cleaned_data
            selection = tokens
        else:
            selection = cleaned_data.get("combination") or ""

        try:
            cleaned_data["combination"] = validate_key_for_product(
                value=selection,
                product=self.event.product,
            )
            self.selected_tokens = self.event.product.key_tokens(
                cleaned_data["combination"]
            )
        except forms.ValidationError as exc:
            self.add_error(None, exc)

        return cleaned_data



class DrawResultPublishForm(forms.Form):
    """Publica un resultado usando una casilla por posición y un motivo."""

    winning_key = forms.CharField(required=False, widget=forms.HiddenInput())
    reason = forms.CharField(
        label="Motivo administrativo",
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=(
            "Explique brevemente cómo se verificó el resultado antes de "
            "publicarlo. El resultado será inmutable."
        ),
    )

    def __init__(self, *args, event, **kwargs):
        self.event = event
        super().__init__(*args, **kwargs)
        _apply_bootstrap_widgets(self)

        choices = tuple(
            (token, token) for token in event.product.symbol_tokens
        )
        self.position_field_names = []
        for index in range(1, event.product.selection_count + 1):
            field_name = f"position_{index}"
            self.position_field_names.append(field_name)
            self.fields[field_name] = forms.ChoiceField(
                label=f"Posición {index}",
                choices=(("", "Seleccione"),) + choices,
                required=True,
                error_messages={
                    "required": "Seleccione un símbolo.",
                    "invalid_choice": (
                        "El símbolo seleccionado no pertenece al producto."
                    ),
                },
                widget=forms.Select(
                    attrs={
                        "class": "form-select font-monospace text-center",
                        "data-result-position": str(index),
                    }
                ),
            )

    @property
    def position_fields(self):
        return [self[field_name] for field_name in self.position_field_names]

    def clean_reason(self):
        reason = (self.cleaned_data.get("reason") or "").strip()
        if not reason:
            raise forms.ValidationError(
                "La publicación requiere un motivo administrativo."
            )
        return reason

    def clean(self):
        cleaned_data = super().clean()
        has_position_payload = any(
            field_name in self.data for field_name in self.position_field_names
        )

        if has_position_payload:
            tokens = [
                cleaned_data.get(field_name) or ""
                for field_name in self.position_field_names
            ]
            if any(
                field_name in self.errors
                for field_name in self.position_field_names
            ):
                return cleaned_data
            selection = tokens
        else:
            selection = cleaned_data.get("winning_key") or ""

        try:
            cleaned_data["winning_key"] = validate_key_for_product(
                value=selection,
                product=self.event.product,
            )
        except forms.ValidationError as exc:
            self.add_error(None, exc)

        return cleaned_data


class DrawEventSeriesForm(forms.ModelForm):
    """Configura una serie editable, limitada o sin límite."""

    class OccurrenceMode:
        UNLIMITED = "UNLIMITED"
        LIMITED = "LIMITED"
        choices = (
            (UNLIMITED, "Sin límite"),
            (LIMITED, "Número limitado"),
        )

    occurrence_mode = forms.ChoiceField(
        label="Duración de la serie",
        choices=OccurrenceMode.choices,
        widget=forms.RadioSelect,
        initial=OccurrenceMode.UNLIMITED,
    )
    result_mode = forms.ChoiceField(
        label="Publicación del resultado",
        choices=DrawEventSeries.ResultMode.choices,
        widget=forms.RadioSelect,
        initial=DrawEventSeries.ResultMode.MANUAL,
        required=False,
    )
    remaining_occurrences = forms.IntegerField(
        label="Sorteos que faltan por generar",
        min_value=0,
        required=False,
        help_text=(
            "Puede cambiar este número después. Cero detiene la generación."
        ),
    )
    price_minor = forms.DecimalField(
        label="Precio del boleto (VIRTUAL)",
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        help_text="Valor en unidades VIRTUAL, por ejemplo 1.50.",
    )
    prize_minor = forms.DecimalField(
        label="Premio fijo (VIRTUAL)",
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        help_text="Premio en unidades VIRTUAL, por ejemplo 50.00.",
    )

    class Meta:
        model = DrawEventSeries
        fields = (
            "name_prefix",
            "product",
            "first_draw_at",
            "next_draw_at",
            "recurrence_minutes",
            "sales_lead_minutes",
            "price_minor",
            "prize_minor",
            "future_events_target",
            "result_mode",
            "occurrence_mode",
            "remaining_occurrences",
            "is_active",
        )
        widgets = {
            "first_draw_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "next_draw_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "recurrence_minutes": forms.NumberInput(attrs={"min": 10}),
            "sales_lead_minutes": forms.NumberInput(attrs={"min": 11}),
            "future_events_target": forms.NumberInput(attrs={"min": 1, "max": 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap_widgets(self)
        self.fields["first_draw_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["next_draw_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["product"].queryset = LotteryProduct.objects.filter(
            is_active=True,
        ).order_by("name", "id")
        self.fields["recurrence_minutes"].help_text = (
            "60 = cada hora, 1440 = cada día, 10080 = cada semana."
        )
        self.fields["sales_lead_minutes"].help_text = (
            "Cuántos minutos antes del sorteo aparecerá para comprar."
        )
        self.fields["future_events_target"].help_text = (
            "Cantidad simultánea de eventos futuros visibles, entre 1 y 10."
        )
        self.fields["result_mode"].help_text = (
            "Manual requiere publicación del Administrador. Automático genera, "
            "publica y liquida el resultado al llegar la hora del sorteo."
        )
        self.fields["next_draw_at"].required = False
        self.fields["next_draw_at"].help_text = (
            "Al editar, cambia la fecha del siguiente evento aún no generado."
        )

        if self.instance.pk:
            self.initial["price_minor"] = Decimal(self.instance.price_minor) / Decimal("100")
            self.initial["prize_minor"] = Decimal(self.instance.prize_minor) / Decimal("100")
            self.initial["occurrence_mode"] = (
                self.OccurrenceMode.UNLIMITED
                if self.instance.remaining_occurrences is None
                else self.OccurrenceMode.LIMITED
            )
            self.initial["remaining_occurrences"] = self.instance.remaining_occurrences
            if self.instance.events.exists():
                self.fields["product"].disabled = True
                self.fields["first_draw_at"].disabled = True
                self.fields["product"].help_text = "No cambia después de generar eventos."
                self.fields["first_draw_at"].help_text = "No cambia después de generar eventos."
        else:
            self.initial.setdefault("next_draw_at", self.initial.get("first_draw_at"))

    def clean_result_mode(self):
        result_mode = (
            self.cleaned_data.get("result_mode")
            or getattr(self.instance, "result_mode", "")
            or DrawEventSeries.ResultMode.MANUAL
        )

        valid_modes = {
            value
            for value, _label in DrawEventSeries.ResultMode.choices
        }

        if result_mode not in valid_modes:
            raise forms.ValidationError(
                "Seleccione un modo de publicación válido."
            )

        return result_mode
    
    def clean(self):
        cleaned = super().clean()
        recurrence = cleaned.get("recurrence_minutes")
        lead = cleaned.get("sales_lead_minutes")
        first_draw = cleaned.get("first_draw_at")
        next_draw = cleaned.get("next_draw_at") or first_draw
        mode = cleaned.get("occurrence_mode")
        remaining = cleaned.get("remaining_occurrences")

        if recurrence and lead and lead > recurrence:
            self.add_error(
                "sales_lead_minutes",
                "La anticipación de ventas no puede superar la frecuencia.",
            )
        if first_draw and not self.instance.pk and first_draw <= timezone.now():
            self.add_error("first_draw_at", "El primer sorteo debe estar en el futuro.")
        if next_draw and next_draw <= timezone.now():
            self.add_error(
                "next_draw_at",
                "El próximo sorteo a generar debe estar en el futuro.",
            )
        if mode == self.OccurrenceMode.LIMITED and remaining is None:
            self.add_error(
                "remaining_occurrences",
                "Indique cuántos sorteos faltan por generar.",
            )
        if mode == self.OccurrenceMode.UNLIMITED:
            cleaned["remaining_occurrences"] = None
        cleaned["next_draw_at"] = next_draw
        return cleaned

    def save(self, commit=True):
        series = super().save(commit=False)

        series.price_minor = int(
            self.cleaned_data["price_minor"] * Decimal("100")
        )
        series.prize_minor = int(
            self.cleaned_data["prize_minor"] * Decimal("100")
        )
        series.result_mode = (
            self.cleaned_data.get("result_mode")
            or DrawEventSeries.ResultMode.MANUAL
        )
        series.remaining_occurrences = self.cleaned_data.get(
            "remaining_occurrences"
        )
        series.next_draw_at = (
            self.cleaned_data.get("next_draw_at")
            or series.first_draw_at
        )

        if series.remaining_occurrences == 0:
            series.is_active = False

        if commit:
            series.full_clean()
            series.save()
            self.save_m2m()

        return series

