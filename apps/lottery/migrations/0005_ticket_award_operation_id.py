# Generated for Taller #3; portable between SQLite and MySQL.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lottery", "0004_tokenized_symbols_and_canonical_keys"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="award_operation_id",
            field=models.UUIDField(
                blank=True,
                editable=False,
                null=True,
                unique=True,
                verbose_name="operación de premio",
            ),
        ),
    ]
