from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lottery", "0010_draweventseries_last_synced_at"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="drawevent",
            name="lot_event_unique_series_sequence",
        ),
        migrations.AddConstraint(
            model_name="drawevent",
            constraint=models.UniqueConstraint(
                fields=("series", "series_sequence"),
                name="lot_event_unique_series_sequence",
            ),
        ),
    ]
