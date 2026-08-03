from django.core.management.base import BaseCommand, CommandError

from apps.lottery.services import (
    process_active_event_series,
    process_due_automatic_results,
    sync_lottery_event_states,
)


class Command(BaseCommand):
    help = (
        "Sincroniza estados, mantiene series activas y procesa resultados "
        "automáticos. Devuelve error si alguna unidad no pudo completarse."
    )

    def handle(self, *args, **options):
        state_changes = sync_lottery_event_states(actor=None)
        series_batch = process_active_event_series(actor=None)
        created = sum(
            len(result.created_event_ids)
            for result in series_batch.results
        )
        skipped = sum(
            result.skipped_sequences
            for result in series_batch.results
        )
        automatic = process_due_automatic_results()
        errors = [
            f"Serie {error.series_id}: {error.message}"
            for error in series_batch.errors
        ]
        errors.extend(automatic.errors)

        self.stdout.write(
            self.style.SUCCESS(
                "Procesamiento terminado: "
                f"estados={state_changes}, "
                f"series_procesadas={len(series_batch.results)}, "
                f"eventos_creados={created}, "
                f"secuencias_omitidas={skipped}, "
                f"resultados_automaticos={len(automatic.processed_event_ids)}, "
                f"resultados_omitidos={len(automatic.skipped_event_ids)}, "
                f"errores={len(errors)}."
            )
        )
        for error in errors:
            self.stderr.write(self.style.ERROR(error))

        if errors:
            raise CommandError(
                "El procesamiento terminó con errores; revise stderr."
            )
