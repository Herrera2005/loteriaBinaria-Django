"""Disponibilidad de combinaciones bajo demanda para P-35B-R3.

No precarga todas las combinaciones. Calcula capacidad con combinatoria y
contrasta únicamente contra los boletos históricos ya persistidos del evento.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import comb

from django.core.exceptions import ValidationError

from .models import DrawEvent, LotteryProduct, Ticket, split_lottery_key, validate_key_for_product


@dataclass(frozen=True)
class CombinationAvailability:
    selected_tokens: tuple[str, ...]
    total_matching: int
    sold_matching: int
    available_matching: int
    suggestions: tuple[tuple[str, ...], ...]

    @property
    def is_complete(self) -> bool:
        return bool(self.selected_tokens) and self.total_matching == 1

    @property
    def is_available(self) -> bool:
        return self.available_matching > 0


def validate_partial_selection(*, product: LotteryProduct, tokens) -> tuple[str, ...]:
    """Valida una selección incompleta sin exigir todavía cardinalidad exacta."""
    normalized = tuple(str(token or "").strip().upper() for token in tokens if str(token or "").strip())
    allowed = product.symbol_tokens
    allowed_set = set(allowed)

    if not normalized:
        raise ValidationError("Seleccione al menos un símbolo para consultar disponibilidad.")

    invalid = sorted(set(normalized) - allowed_set)
    if invalid:
        raise ValidationError(
            "La selección contiene símbolos no permitidos: " + ", ".join(invalid) + "."
        )

    if len(set(normalized)) != len(normalized):
        raise ValidationError("No puede repetir un símbolo en varias posiciones.")

    if len(normalized) > product.selection_count:
        raise ValidationError(
            f"La selección no puede superar {product.selection_count} posiciones."
        )

    order = {token: index for index, token in enumerate(allowed)}
    return tuple(sorted(normalized, key=order.__getitem__))


def _sold_keys_for_event(event: DrawEvent) -> set[str]:
    # Los boletos son históricos: una combinación vendida permanece ocupada.
    return set(
        Ticket.objects.filter(event=event).values_list("normalized_key", flat=True)
    )


def _sold_matching_partial(*, event: DrawEvent, selected: tuple[str, ...]) -> int:
    selected_set = set(selected)
    count = 0
    for key in _sold_keys_for_event(event):
        tokens = set(split_lottery_key(value=key, product=event.product))
        if selected_set.issubset(tokens):
            count += 1
    return count


def _suggest_available(
    *,
    event: DrawEvent,
    selected: tuple[str, ...],
    limit: int,
    scan_limit: int = 20000,
) -> tuple[tuple[str, ...], ...]:
    product = event.product
    remaining_needed = product.selection_count - len(selected)
    sold = _sold_keys_for_event(event)
    remaining = tuple(token for token in product.symbol_tokens if token not in selected)
    suggestions: list[tuple[str, ...]] = []

    if remaining_needed == 0:
        canonical = validate_key_for_product(value=selected, product=product)
        return (selected,) if canonical not in sold else ()

    scanned = 0
    for suffix in combinations(remaining, remaining_needed):
        scanned += 1
        candidate = selected + suffix
        canonical = validate_key_for_product(value=candidate, product=product)
        if canonical not in sold:
            suggestions.append(split_lottery_key(value=canonical, product=product))
            if len(suggestions) >= limit:
                break
        if scanned >= scan_limit:
            break

    return tuple(suggestions)


def get_combination_availability(
    *,
    event: DrawEvent,
    selected_tokens=(),
    suggestion_limit: int = 8,
) -> CombinationAvailability:
    """Calcula disponibilidad exacta sin materializar el universo completo."""
    selected = validate_partial_selection(
        product=event.product,
        tokens=selected_tokens,
    )
    remaining_needed = event.product.selection_count - len(selected)
    remaining_symbols = event.product.symbol_count - len(selected)
    total_matching = comb(remaining_symbols, remaining_needed)
    sold_matching = _sold_matching_partial(event=event, selected=selected)
    available_matching = max(total_matching - sold_matching, 0)
    suggestions = _suggest_available(
        event=event,
        selected=selected,
        limit=max(0, suggestion_limit),
    ) if available_matching else ()

    return CombinationAvailability(
        selected_tokens=selected,
        total_matching=total_matching,
        sold_matching=sold_matching,
        available_matching=available_matching,
        suggestions=suggestions,
    )
