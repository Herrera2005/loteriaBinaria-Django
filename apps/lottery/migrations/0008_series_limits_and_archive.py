from django.db import migrations, models
from datetime import timedelta


def populate_next_draw_at(apps, schema_editor):
    DrawEventSeries = apps.get_model("lottery", "DrawEventSeries")
    for series in DrawEventSeries.objects.all().iterator():
        series.next_draw_at = series.first_draw_at + timedelta(
            minutes=series.recurrence_minutes * (series.next_sequence - 1),
        )
        series.save(update_fields=("next_draw_at",))


class Migration(migrations.Migration):
    dependencies = [
        ("lottery", "0007_event_series"),
    ]

    operations = [
        migrations.AddField(
            model_name="draweventseries",
            name="archived_at",
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name="eliminada el"),
        ),
        migrations.AddField(
            model_name="draweventseries",
            name="is_archived",
            field=models.BooleanField(db_index=True, default=False, verbose_name="programación eliminada"),
        ),
        migrations.AddField(
            model_name="draweventseries",
            name="next_draw_at",
            field=models.DateTimeField(blank=True, help_text="Permite reprogramar únicamente los eventos que todavía no se han generado.", null=True, verbose_name="próximo sorteo a generar"),
        ),
        migrations.AddField(
            model_name="draweventseries",
            name="remaining_occurrences",
            field=models.PositiveIntegerField(blank=True, help_text="Vacío significa sin límite.", null=True, verbose_name="generaciones restantes"),
        ),
        migrations.RunPython(populate_next_draw_at, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="draweventseries",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(remaining_occurrences__isnull=True)
                    | models.Q(remaining_occurrences__gte=0)
                ),
                name="lot_series_remaining_nonnegative",
            ),
        ),
    ]
