from django.core.management.base import BaseCommand

from apps.lottery.services import sync_lottery_event_states


class Command(BaseCommand):
    help = "Abre y cierra ventas según la hora del servidor."

    def handle(self, *args, **options):
        changed = sync_lottery_event_states()
        self.stdout.write(
            self.style.SUCCESS(f"Eventos sincronizados: {changed}")
        )
