from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("lottery", "0008_series_limits_and_archive"),
    ]

    operations = [
        migrations.AddField(
            model_name="draweventseries",
            name="result_mode",
            field=models.CharField(
                choices=[
                    ("MANUAL", "Manual por Administrador"),
                    ("AUTOMATIC", "Automático por el sistema"),
                ],
                db_index=True,
                default="MANUAL",
                max_length=20,
                verbose_name="publicación del resultado",
            ),
        ),
        migrations.AlterField(
            model_name="drawresult",
            name="published_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="published_draw_results",
                to=settings.AUTH_USER_MODEL,
                verbose_name="publicado por",
            ),
        ),
        migrations.AddField(
            model_name="drawresult",
            name="publication_source",
            field=models.CharField(
                choices=[
                    ("ADMINISTRATOR", "Administrador"),
                    ("SYSTEM", "Sistema"),
                ],
                db_index=True,
                default="ADMINISTRATOR",
                max_length=20,
                verbose_name="origen de publicación",
            ),
        ),
    ]
