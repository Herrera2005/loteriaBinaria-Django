from django.db import migrations, models
import django.core.validators


def set_existing_product_colors(apps, schema_editor):
    LotteryProduct = apps.get_model("lottery", "LotteryProduct")
    colors = {
        "OCTAL": "#0D6EFD",
        "DECIMAL": "#198754",
        "HEXADECIMAL": "#6F42C1",
    }
    for code, color in colors.items():
        LotteryProduct.objects.filter(code=code).update(accent_color=color)


def reset_existing_product_colors(apps, schema_editor):
    LotteryProduct = apps.get_model("lottery", "LotteryProduct")
    LotteryProduct.objects.all().update(accent_color="#FD7E14")


class Migration(migrations.Migration):
    dependencies = [("lottery", "0005_ticket_award_operation_id")]
    operations = [
        migrations.AddField(
            model_name="lotteryproduct",
            name="accent_color",
            field=models.CharField(
                default="#FD7E14",
                help_text="Color hexadecimal usado en bordes y símbolos, por ejemplo #0D6EFD.",
                max_length=7,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Ingrese un color hexadecimal válido, por ejemplo #0D6EFD.",
                        regex="^#[0-9A-Fa-f]{6}$",
                    )
                ],
                verbose_name="color identificador",
            ),
        ),
        migrations.RunPython(
            set_existing_product_colors,
            reset_existing_product_colors,
        ),
    ]
