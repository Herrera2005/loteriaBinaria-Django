from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lottery", "0009_automatic_results"),
    ]

    operations = [
        migrations.AddField(
            model_name="draweventseries",
            name="last_synced_at",
            field=models.DateTimeField(
                blank=True,
                editable=False,
                help_text=(
                    "Fecha del último intento real de procesar la serie mediante "
                    "el servicio de generación, incluso cuando no se creen eventos."
                ),
                null=True,
                verbose_name="última sincronización",
            ),
        ),
    ]
