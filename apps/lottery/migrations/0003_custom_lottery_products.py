# Generated for Taller #3; portable between SQLite and MySQL.

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lottery", "0002_draweventstatustransition"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="lotteryproduct",
            name="lot_prod_selection_gt_0",
        ),
        migrations.RemoveConstraint(
            model_name="lotteryproduct",
            name="lot_prod_valid_config",
        ),
        migrations.AddField(
            model_name="lotteryproduct",
            name="kind",
            field=models.CharField(
                choices=[
                    ("OFFICIAL", "Oficial"),
                    ("CUSTOM", "Personalizado"),
                ],
                db_index=True,
                default="OFFICIAL",
                max_length=12,
                verbose_name="tipo de configuración",
            ),
        ),
        migrations.AlterField(
            model_name="lotteryproduct",
            name="code",
            field=models.CharField(
                max_length=20,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message=(
                            "El código solo puede contener letras, números "
                            "y guion bajo."
                        ),
                        regex="^[A-Z0-9_]+$",
                    )
                ],
                verbose_name="código",
            ),
        ),
        migrations.AlterField(
            model_name="lotteryproduct",
            name="selection_count",
            field=models.PositiveSmallIntegerField(
                verbose_name="cantidad de posiciones",
            ),
        ),
        migrations.AddConstraint(
            model_name="lotteryproduct",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("selection_count__gte", 2),
                    ("selection_count__lte", 8),
                ),
                name="lot_prod_selection_2_8",
            ),
        ),
        migrations.AddConstraint(
            model_name="lotteryproduct",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        ("allowed_symbols", "01234567"),
                        ("code", "OCTAL"),
                        ("kind", "OFFICIAL"),
                        ("selection_count", 4),
                    )
                    | models.Q(
                        ("allowed_symbols", "0123456789"),
                        ("code", "DECIMAL"),
                        ("kind", "OFFICIAL"),
                        ("selection_count", 5),
                    )
                    | models.Q(
                        ("allowed_symbols", "0123456789ABCDEF"),
                        ("code", "HEXADECIMAL"),
                        ("kind", "OFFICIAL"),
                        ("selection_count", 6),
                    )
                    | (
                        models.Q(("kind", "CUSTOM"))
                        & ~models.Q(
                            (
                                "code__in",
                                ("OCTAL", "DECIMAL", "HEXADECIMAL"),
                            )
                        )
                    )
                ),
                name="lot_prod_valid_config",
            ),
        ),
    ]
