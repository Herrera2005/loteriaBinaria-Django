"""Formularios del CRUD evaluable de productos y eventos."""

from __future__ import annotations

from django import forms

from .models import DrawEvent, LotteryProduct


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
    """Crea o edita las tres configuraciones oficiales."""

    class Meta:
        model = LotteryProduct
        fields = (
            "code",
            "name",
            "allowed_symbols",
            "selection_count",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap_widgets(self)

        self.fields["allowed_symbols"].help_text = (
            "OCTAL: 01234567; DECIMAL: 0123456789; "
            "HEXADECIMAL: 0123456789ABCDEF."
        )
        self.fields["selection_count"].help_text = (
            "OCTAL: 4; DECIMAL: 5; HEXADECIMAL: 6."
        )

        if self.instance.pk and self.instance.events.exists():
            self.fields["code"].disabled = True
            self.fields["allowed_symbols"].disabled = True
            self.fields["selection_count"].disabled = True
            self.fields["code"].help_text = (
                "La configuración no cambia cuando ya existen eventos."
            )

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get("code")
        allowed_symbols = cleaned_data.get("allowed_symbols")
        selection_count = cleaned_data.get("selection_count")

        if not code:
            return cleaned_data

        rule = LotteryProduct.rule_for_code(code)
        product_labels = dict(LotteryProduct.Code.choices)

        if allowed_symbols != rule["allowed_symbols"]:
            self.add_error(
                "allowed_symbols",
                (
                    f"{product_labels[code]} debe usar "
                    f"{rule['allowed_symbols']}."
                ),
            )

        if selection_count != rule["selection_count"]:
            self.add_error(
                "selection_count",
                (
                    f"{product_labels[code]} requiere "
                    f"{rule['selection_count']} símbolos únicos."
                ),
            )

        return cleaned_data


class DrawEventForm(forms.ModelForm):
    """Administra el evento; el cierre se calcula en el backend."""

    PROTECTED_AFTER_DRAFT = (
        "product",
        "sales_open_at",
        "draw_at",
        "price_minor",
        "prize_minor",
        "status",
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
            "status",
            "cancellation_reason",
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
            "cancellation_reason": forms.Textarea(
                attrs={"rows": 3},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap_widgets(self)

        self.fields["sales_open_at"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]
        self.fields["draw_at"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]
        self.fields["draw_at"].help_text = (
            "El cierre se calculará automáticamente diez minutos antes."
        )
        self.fields["price_minor"].help_text = (
            "Monto entero en unidades menores; nunca float."
        )
        self.fields["prize_minor"].help_text = (
            "Premio fijo entero en unidades menores."
        )

        self._protected_original_values = {}

        if (
            self.instance.pk
            and self.instance.status != DrawEvent.Status.DRAFT
        ):
            self.fields["status"].help_text = (
                "Las transiciones posteriores a Borrador requieren una "
                "acción específica; el CRUD normal conserva el estado."
            )
            for field_name in self.PROTECTED_AFTER_DRAFT:
                self._protected_original_values[field_name] = getattr(
                    self.instance,
                    field_name,
                )
                self.fields[field_name].disabled = True

    def clean(self):
        cleaned_data = super().clean()

        if self._protected_original_values:
            for field_name, original_value in (
                self._protected_original_values.items()
            ):
                cleaned_data[field_name] = original_value
                setattr(self.instance, field_name, original_value)

        sales_open_at = cleaned_data.get("sales_open_at")
        draw_at = cleaned_data.get("draw_at")
        status = cleaned_data.get("status")
        cancellation_reason = (
            cleaned_data.get("cancellation_reason") or ""
        ).strip()

        if draw_at is not None:
            sales_close_at = DrawEvent.calculate_sales_close_at(
                draw_at
            )
            self.instance.sales_close_at = sales_close_at

            if (
                sales_open_at is not None
                and sales_open_at >= sales_close_at
            ):
                self.add_error(
                    "sales_open_at",
                    (
                        "La apertura debe ser anterior al cierre, que ocurre "
                        "diez minutos antes del sorteo."
                    ),
                )

        if (
            status == DrawEvent.Status.CANCELLED
            and not cancellation_reason
        ):
            self.add_error(
                "cancellation_reason",
                "Un evento cancelado requiere un motivo.",
            )

        if (
            status != DrawEvent.Status.CANCELLED
            and cancellation_reason
        ):
            self.add_error(
                "cancellation_reason",
                "El motivo solo corresponde a eventos cancelados.",
            )

        return cleaned_data

    def save(self, commit=True):
        event = super().save(commit=False)

        if self._protected_original_values:
            for field_name, original_value in (
                self._protected_original_values.items()
            ):
                setattr(event, field_name, original_value)

        event.sales_close_at = DrawEvent.calculate_sales_close_at(
            event.draw_at
        )

        if commit:
            event.full_clean()
            event.save()
            self.save_m2m()

        return event
