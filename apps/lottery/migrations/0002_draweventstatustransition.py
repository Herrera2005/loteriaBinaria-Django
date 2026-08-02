from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("lottery", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DrawEventStatusTransition",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("from_status", models.CharField(choices=[("DRAFT", "Borrador"), ("SCHEDULED", "Programado"), ("PUBLISHED", "Publicado"), ("SALES_OPEN", "Ventas abiertas"), ("SALES_CLOSED", "Ventas cerradas"), ("RESULT_SET", "Resultado fijado"), ("FINISHED", "Finalizado"), ("CANCELLED", "Cancelado")], max_length=30, verbose_name="estado anterior")),
                ("to_status", models.CharField(choices=[("DRAFT", "Borrador"), ("SCHEDULED", "Programado"), ("PUBLISHED", "Publicado"), ("SALES_OPEN", "Ventas abiertas"), ("SALES_CLOSED", "Ventas cerradas"), ("RESULT_SET", "Resultado fijado"), ("FINISHED", "Finalizado"), ("CANCELLED", "Cancelado")], max_length=30, verbose_name="estado nuevo")),
                ("reason", models.TextField(verbose_name="motivo administrativo")),
                ("public_message", models.TextField(blank=True, verbose_name="mensaje público")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="creado")),
                ("changed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="lottery_status_transitions", to=settings.AUTH_USER_MODEL, verbose_name="cambiado por")),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="status_transitions", to="lottery.drawevent", verbose_name="evento")),
            ],
            options={
                "verbose_name": "transición de estado",
                "verbose_name_plural": "transiciones de estado",
                "ordering": ("-created_at", "-id"),
            },
        ),
        migrations.AddIndex(
            model_name="draweventstatustransition",
            index=models.Index(fields=["event", "created_at"], name="lot_status_event_date_idx"),
        ),
    ]
