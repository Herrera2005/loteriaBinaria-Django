from __future__ import annotations

from rest_framework import filters
from rest_framework.exceptions import ValidationError


class StrictOrderingFilter(filters.OrderingFilter):
    """
    OrderingFilter estricto.

    A diferencia del filtro por defecto de DRF, no ignora silenciosamente
    campos de ordenamiento inválidos.
    """

    def remove_invalid_fields(
        self,
        queryset,
        fields,
        view,
        request,
    ):
        valid_fields = {
            field
            for field, _label in self.get_valid_fields(
                queryset,
                view,
                {"request": request},
            )
        }

        invalid_fields = []

        for field in fields:
            normalized = field.removeprefix("-")

            if normalized not in valid_fields:
                invalid_fields.append(field)

        if invalid_fields:
            raise ValidationError(
                {
                    self.ordering_param: [
                        (
                            "Campo de ordenamiento no válido: "
                            + ", ".join(invalid_fields)
                            + "."
                        )
                    ]
                }
            )

        return fields