from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.lottery.models import DrawEvent, DrawResult, LotteryProduct


class Command(BaseCommand):
    help = (
        "Crea productos, sorteos y un resultado públicos para demostrar la API. "
        "Es idempotente y no crea usuarios ni credenciales."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        products = self._products()
        events = self._events(products)
        self._result(events["finished"])
        self.stdout.write(
            self.style.SUCCESS(
                "Seed público API listo: 3 productos, 3 sorteos y 1 resultado de demostración."
            )
        )

    def _products(self):
        definitions = {
            "OCTAL": {
                "kind": LotteryProduct.Kind.OFFICIAL,
                "name": "Lotería Octal",
                "allowed_symbols": "01234567",
                "selection_count": 4,
                "accent_color": "#0D6EFD",
            },
            "DECIMAL": {
                "kind": LotteryProduct.Kind.OFFICIAL,
                "name": "Lotería Decimal",
                "allowed_symbols": "0123456789",
                "selection_count": 5,
                "accent_color": "#198754",
            },
            "HEXADECIMAL": {
                "kind": LotteryProduct.Kind.OFFICIAL,
                "name": "Lotería Hexadecimal",
                "allowed_symbols": "0123456789ABCDEF",
                "selection_count": 6,
                "accent_color": "#6F42C1",
            },
        }
        products = {}
        for code, defaults in definitions.items():
            product, _ = LotteryProduct.objects.get_or_create(
                code=code,
                defaults={**defaults, "is_active": True},
            )
            products[code] = product
        return products

    def _events(self, products):
        now = timezone.now()
        definitions = {
            "open": {
                "name": "API Demo — Decimal con ventas abiertas",
                "product": products["DECIMAL"],
                "sales_open_at": now - timedelta(hours=1),
                "draw_at": now + timedelta(days=1),
                "price_minor": 100,
                "prize_minor": 50000,
                "status": DrawEvent.Status.SALES_OPEN,
            },
            "upcoming": {
                "name": "API Demo — Hexadecimal próximo",
                "product": products["HEXADECIMAL"],
                "sales_open_at": now + timedelta(hours=12),
                "draw_at": now + timedelta(days=2),
                "price_minor": 200,
                "prize_minor": 100000,
                "status": DrawEvent.Status.PUBLISHED,
            },
            "finished": {
                "name": "API Demo — Octal finalizado",
                "product": products["OCTAL"],
                "sales_open_at": now - timedelta(days=2),
                "draw_at": now - timedelta(days=1),
                "price_minor": 100,
                "prize_minor": 25000,
                "status": DrawEvent.Status.FINISHED,
            },
        }
        events = {}
        for key, values in definitions.items():
            event = DrawEvent.objects.filter(name=values["name"]).first()
            if event is None:
                event = DrawEvent(
                    **values,
                    sales_close_at=DrawEvent.calculate_sales_close_at(
                        values["draw_at"]
                    ),
                )
                event.full_clean()
                event.save()
            events[key] = event
        return events

    def _result(self, event):
        if hasattr(event, "result"):
            return event.result
        result = DrawResult(
            event=event,
            winning_key="0123",
            publication_source=DrawResult.PublicationSource.SYSTEM,
            reason="Resultado controlado para demostrar la API pública.",
        )
        result.full_clean()
        result.save()
        return result
