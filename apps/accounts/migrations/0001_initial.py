# Generated for the Taller #3 baseline.
# Do not edit this migration after it has been applied.

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="TermsVersion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("TERMS", "Términos y condiciones"),
                            ("PRIVACY", "Política de privacidad"),
                        ],
                        max_length=20,
                        verbose_name="tipo",
                    ),
                ),
                (
                    "version",
                    models.CharField(max_length=30, verbose_name="versión"),
                ),
                (
                    "title",
                    models.CharField(max_length=150, verbose_name="título"),
                ),
                (
                    "content",
                    models.TextField(verbose_name="contenido"),
                ),
                (
                    "effective_at",
                    models.DateTimeField(verbose_name="vigente desde"),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="activa"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="creada",
                    ),
                ),
            ],
            options={
                "verbose_name": "versión de términos",
                "verbose_name_plural": "versiones de términos",
                "ordering": ("-effective_at", "-created_at"),
            },
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "password",
                    models.CharField(max_length=128, verbose_name="password"),
                ),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="last login",
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text=(
                            "Designates that this user has all permissions "
                            "without explicitly assigning them."
                        ),
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text=(
                            "Required. 150 characters or fewer. Letters, "
                            "digits and @/./+/-/_ only."
                        ),
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True,
                        max_length=150,
                        verbose_name="first name",
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True,
                        max_length=150,
                        verbose_name="last name",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        max_length=254,
                        unique=True,
                        verbose_name="correo electrónico",
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text=(
                            "Designates whether the user can log into this "
                            "admin site."
                        ),
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text=(
                            "Designates whether this user should be treated "
                            "as active. Unselect this instead of deleting "
                            "accounts."
                        ),
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name="date joined",
                    ),
                ),
                (
                    "document",
                    models.CharField(
                        max_length=30,
                        unique=True,
                        verbose_name="documento",
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        blank=True,
                        max_length=30,
                        verbose_name="teléfono",
                    ),
                ),
                (
                    "birth_date",
                    models.DateField(verbose_name="fecha de nacimiento"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Activo"),
                            ("SUSPENDED", "Suspendido"),
                            ("BLOCKED", "Bloqueado"),
                            ("DISABLED", "Desactivado"),
                        ],
                        default="ACTIVE",
                        max_length=20,
                        verbose_name="estado",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="creado",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="actualizado",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text=(
                            "The groups this user belongs to. A user will get "
                            "all permissions granted to each of their groups."
                        ),
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "usuario",
                "verbose_name_plural": "usuarios",
                "ordering": ("username",),
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="TermsAcceptance",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "accepted_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="aceptada",
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        blank=True,
                        null=True,
                        verbose_name="dirección IP",
                    ),
                ),
                (
                    "terms_version",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="acceptances",
                        to="accounts.termsversion",
                        verbose_name="versión de términos",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="terms_acceptances",
                        to="accounts.user",
                        verbose_name="usuario",
                    ),
                ),
            ],
            options={
                "verbose_name": "aceptación de términos",
                "verbose_name_plural": "aceptaciones de términos",
                "ordering": ("-accepted_at",),
            },
        ),
        migrations.AddIndex(
            model_name="termsversion",
            index=models.Index(
                fields=["kind", "is_active"],
                name="accounts_terms_kind_active_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="termsversion",
            index=models.Index(
                fields=["effective_at"],
                name="accounts_terms_effective_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="termsversion",
            constraint=models.UniqueConstraint(
                fields=("kind", "version"),
                name="accounts_terms_kind_version_uq",
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["email"],
                name="accounts_user_email_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["document"],
                name="accounts_user_doc_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["status"],
                name="accounts_user_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="termsacceptance",
            index=models.Index(
                fields=["user", "accepted_at"],
                name="accounts_accept_user_date_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="termsacceptance",
            constraint=models.UniqueConstraint(
                fields=("user", "terms_version"),
                name="accounts_accept_user_terms_uq",
            ),
        ),
    ]
