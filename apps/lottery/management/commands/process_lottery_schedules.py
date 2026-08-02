from django.core.management.base import BaseCommand

from apps.lottery.services import (
    process_active_event_series,
    process_due_automatic_results,
    sync_lottery_event_states,
)


class Command(BaseCommand):
    help = "Sincroniza estados y mantiene los eventos futuros de las series activas."

    def handle(self, *args, **options):
        state_changes = sync_lottery_event_states(actor=None)
        results = process_active_event_series(actor=None)
        created = sum(len(result.created_event_ids) for result in results)
        skipped = sum(result.skipped_sequences for result in results)
        automatic = process_due_automatic_results()
        self.stdout.write(
            self.style.SUCCESS(
                "Procesamiento terminado: "
                f"estados={state_changes}, "
                f"eventos_creados={created}, "
                f"secuencias_omitidas={skipped}, "
                f"resultados_automaticos={len(automatic.processed_event_ids)}, "
                f"resultados_omitidos={len(automatic.skipped_event_ids)}, "
                f"errores={len(automatic.errors)}."
            )
        )
        for error in automatic.errors:
            self.stderr.write(self.style.ERROR(error))
