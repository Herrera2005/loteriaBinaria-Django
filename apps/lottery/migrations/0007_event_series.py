from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("lottery", "0006_lotteryproduct_accent_color"),
    ]

    operations = [
        migrations.CreateModel(
            name="DrawEventSeries",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name_prefix", models.CharField(max_length=120, verbose_name="nombre base")),
                ("first_draw_at", models.DateTimeField(verbose_name="primer sorteo")),
                ("recurrence_minutes", models.PositiveIntegerField(help_text="Mínimo 10 minutos.", validators=[django.core.validators.MinValueValidator(10)], verbose_name="frecuencia en minutos")),
                ("sales_lead_minutes", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="anticipación de ventas en minutos")),
                ("price_minor", models.BigIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="precio en unidades menores")),
                ("prize_minor", models.BigIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="premio en unidades menores")),
                ("future_events_target", models.PositiveSmallIntegerField(default=2, validators=[django.core.validators.MinValueValidator(1)], verbose_name="eventos futuros a mantener")),
                ("next_sequence", models.PositiveIntegerField(default=1, editable=False, verbose_name="próxima secuencia")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="activa")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="creada")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="actualizada")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_draw_event_series", to=settings.AUTH_USER_MODEL, verbose_name="creada por")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="event_series", to="lottery.lotteryproduct", verbose_name="producto")),
            ],
            options={
                "verbose_name": "serie de sorteos",
                "verbose_name_plural": "series de sorteos",
                "ordering": ("name_prefix", "id"),
            },
        ),
        migrations.AddField(
            model_name="drawevent",
            name="series",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="events", to="lottery.draweventseries", verbose_name="serie"),
        ),
        migrations.AddField(
            model_name="drawevent",
            name="series_sequence",
            field=models.PositiveIntegerField(blank=True, editable=False, null=True, verbose_name="secuencia de serie"),
        ),
        migrations.AddConstraint(model_name="draweventseries", constraint=models.CheckConstraint(condition=models.Q(("recurrence_minutes__gte", 10)), name="lot_series_recurrence_gte_10")),
        migrations.AddConstraint(model_name="draweventseries", constraint=models.CheckConstraint(condition=models.Q(("sales_lead_minutes__gte", 11)), name="lot_series_lead_gte_11")),
        migrations.AddConstraint(model_name="draweventseries", constraint=models.CheckConstraint(condition=models.Q(("future_events_target__gte", 1), ("future_events_target__lte", 10)), name="lot_series_future_target_1_10")),
        migrations.AddConstraint(model_name="draweventseries", constraint=models.CheckConstraint(condition=models.Q(("price_minor__gt", 0)), name="lot_series_price_gt_0")),
        migrations.AddConstraint(model_name="draweventseries", constraint=models.CheckConstraint(condition=models.Q(("prize_minor__gt", 0)), name="lot_series_prize_gt_0")),
        migrations.AddConstraint(model_name="drawevent", constraint=models.CheckConstraint(condition=models.Q(models.Q(("series__isnull", True), ("series_sequence__isnull", True)), models.Q(("series__isnull", False), ("series_sequence__isnull", False)), _connector="OR"), name="lot_event_series_pair")),
        migrations.AddConstraint(model_name="drawevent", constraint=models.UniqueConstraint(condition=models.Q(("series__isnull", False)), fields=("series", "series_sequence"), name="lot_event_unique_series_sequence")),
        migrations.AddIndex(model_name="drawevent", index=models.Index(fields=["series", "series_sequence"], name="lot_event_series_seq_idx")),
    ]
