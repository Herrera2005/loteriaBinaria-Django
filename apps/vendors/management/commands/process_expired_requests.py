"""Procesa solicitudes REAL → VIRTUAL cuyo plazo terminó."""

from django.core.management.base import BaseCommand

from apps.vendors.services import process_expired_conversion_requests


class Command(BaseCommand):
    help = (
        "Libera reservas de solicitudes de conversión vencidas y las marca "
        "como expiradas. Es seguro ejecutarlo repetidamente."
    )

    def handle(self, *args, **options):
        processed = process_expired_conversion_requests()
        self.stdout.write(
            self.style.SUCCESS(
                f"Solicitudes vencidas procesadas: {processed}"
            )
        )
