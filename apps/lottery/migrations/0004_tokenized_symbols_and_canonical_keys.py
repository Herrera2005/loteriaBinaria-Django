# Generated for Taller #3; portable between SQLite and MySQL.

from django.db import migrations, models


SEPARATOR = "|"


def _product_tokens(kind, stored_value):
    raw = (stored_value or "").strip().upper()
    if kind == "OFFICIAL":
        return tuple(raw)
    if SEPARATOR in raw:
        return tuple(part for part in raw.split(SEPARATOR) if part)
    return tuple(raw)


def _canonical_key(raw_value, tokens, selection_count):
    raw = (raw_value or "").strip().upper()
    if SEPARATOR in raw:
        selected = tuple(part for part in raw.split(SEPARATOR) if part)
    elif tokens and all(len(token) == 1 for token in tokens):
        selected = tuple(raw)
    else:
        selected = (raw,) if raw else ()

    if len(selected) != selection_count:
        raise RuntimeError(
            "No se puede normalizar una combinación histórica con longitud inválida."
        )
    if len(set(selected)) != len(selected):
        raise RuntimeError(
            "No se puede normalizar una combinación histórica con símbolos repetidos."
        )
    if set(selected) - set(tokens):
        raise RuntimeError(
            "No se puede normalizar una combinación histórica fuera del universo."
        )

    order = {token: index for index, token in enumerate(tokens)}
    canonical = tuple(sorted(selected, key=order.__getitem__))
    if all(len(token) == 1 for token in canonical):
        return "".join(canonical)
    return SEPARATOR.join(canonical)


def tokenize_custom_products_and_keys(apps, schema_editor):
    LotteryProduct = apps.get_model("lottery", "LotteryProduct")
    DrawEvent = apps.get_model("lottery", "DrawEvent")
    Ticket = apps.get_model("lottery", "Ticket")
    DrawResult = apps.get_model("lottery", "DrawResult")

    products = list(LotteryProduct.objects.all().order_by("id"))
    product_tokens = {}
    products_to_update = []

    for product in products:
        tokens = _product_tokens(product.kind, product.allowed_symbols)
        if product.kind == "CUSTOM":
            serialized = SEPARATOR.join(tokens)
            if product.allowed_symbols != serialized:
                product.allowed_symbols = serialized
                products_to_update.append(product)
        product_tokens[product.pk] = (tokens, product.selection_count)

    if products_to_update:
        LotteryProduct.objects.bulk_update(
            products_to_update,
            ["allowed_symbols"],
        )

    event_products = dict(
        DrawEvent.objects.values_list("id", "product_id")
    )

    tickets = list(Ticket.objects.all().order_by("id"))
    seen_ticket_keys = {}
    tickets_to_update = []
    for ticket in tickets:
        product_id = event_products[ticket.event_id]
        tokens, selection_count = product_tokens[product_id]
        canonical = _canonical_key(
            ticket.normalized_key,
            tokens,
            selection_count,
        )
        unique_key = (ticket.event_id, canonical)
        previous_id = seen_ticket_keys.get(unique_key)
        if previous_id is not None:
            raise RuntimeError(
                "Existen boletos históricos equivalentes por permutación "
                f"(IDs {previous_id} y {ticket.pk}). Resuelva el conflicto "
                "antes de aplicar la migración."
            )
        seen_ticket_keys[unique_key] = ticket.pk
        if ticket.normalized_key != canonical:
            ticket.normalized_key = canonical
            tickets_to_update.append(ticket)

    if tickets_to_update:
        Ticket.objects.bulk_update(tickets_to_update, ["normalized_key"])

    results_to_update = []
    for result in DrawResult.objects.all().order_by("id"):
        product_id = event_products[result.event_id]
        tokens, selection_count = product_tokens[product_id]
        canonical = _canonical_key(
            result.winning_key,
            tokens,
            selection_count,
        )
        if result.winning_key != canonical:
            result.winning_key = canonical
            results_to_update.append(result)

    if results_to_update:
        DrawResult.objects.bulk_update(results_to_update, ["winning_key"])


class Migration(migrations.Migration):

    dependencies = [
        ("lottery", "0003_custom_lottery_products"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lotteryproduct",
            name="allowed_symbols",
            field=models.CharField(
                max_length=95,
                verbose_name="símbolos permitidos",
            ),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="normalized_key",
            field=models.CharField(
                max_length=64,
                verbose_name="combinación normalizada",
            ),
        ),
        migrations.AlterField(
            model_name="drawresult",
            name="winning_key",
            field=models.CharField(
                max_length=64,
                verbose_name="combinación ganadora",
            ),
        ),
        migrations.RunPython(
            tokenize_custom_products_and_keys,
            migrations.RunPython.noop,
        ),
    ]
