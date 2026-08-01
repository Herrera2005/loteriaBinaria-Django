from __future__ import annotations

from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import TermsAcceptance
from apps.accounts.roles import ADMINISTRATOR, CLIENT, VENDOR
from apps.core.seed import ensure_legal_versions, ensure_role_groups


def years_ago(years: int) -> date:
    today = timezone.localdate()
    try:
        return today.replace(year=today.year - years)
    except ValueError:
        return today.replace(year=today.year - years, month=2, day=28)


class Command(BaseCommand):
    help = (
        "Crea usuarios demo locales de forma idempotente. Requiere DEBUG=True "
        "y DJANGO_DEMO_PASSWORD."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo solo se permite con DEBUG=True.")
        password = settings.DEMO_PASSWORD
        if not password:
            raise CommandError(
                "Configura DJANGO_DEMO_PASSWORD en .env antes de usar seed_demo."
            )
        try:
            validate_password(password)
        except ValidationError as exc:
            details = "; ".join(exc.messages)
            raise CommandError(
                f"DJANGO_DEMO_PASSWORD no es válida: {details}"
            ) from exc

        groups = ensure_role_groups()
        terms = ensure_legal_versions()
        users = self._upsert_users(groups, password)
        for user in users.values():
            for version in terms.values():
                TermsAcceptance.objects.get_or_create(
                    user=user,
                    terms_version=version,
                    defaults={"ip_address": "127.0.0.1"},
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed demo local completado sin imprimir credenciales."
            )
        )

    def _upsert_users(self, groups, password):
        User = get_user_model()
        definitions = (
            (
                "client",
                "cliente_demo",
                "cliente.demo@example.test",
                "DEMO-CLIENTE-001",
                25,
                (CLIENT,),
                False,
                False,
            ),
            (
                "vendor",
                "vendedor_demo",
                "vendedor.demo@example.test",
                "DEMO-VENDEDOR-001",
                30,
                (VENDOR,),
                False,
                False,
            ),
            (
                "multirole",
                "multirole_demo",
                "multirole.demo@example.test",
                "DEMO-MULTIROL-001",
                28,
                (CLIENT, VENDOR),
                False,
                False,
            ),
            (
                "admin",
                "admin_demo",
                "admin.demo@example.test",
                "DEMO-ADMIN-001",
                35,
                (ADMINISTRATOR,),
                True,
                True,
            ),
        )
        users = {}
        for key, username, email, document, age, role_names, staff, superuser in definitions:
            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    "email": email,
                    "document": document,
                    "phone": "",
                    "birth_date": years_ago(age),
                    "first_name": username.split("_")[0].title(),
                    "last_name": "Demo",
                    "status": User.Status.ACTIVE,
                    "is_active": True,
                    "is_staff": staff,
                    "is_superuser": superuser,
                },
            )
            if not user.check_password(password):
                user.set_password(password)
                user.save(update_fields=("password",))
            user.groups.set(groups[name] for name in role_names)
            users[key] = user
        return users
