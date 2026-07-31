from __future__ import annotations

from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import TermsAcceptance, TermsVersion


DEMO_PASSWORD = "T3cn0l0g1@"


def years_ago(years: int) -> date:
    """Devuelve una fecha relativa estable, incluyendo el 29 de febrero."""
    today = timezone.localdate()

    try:
        return today.replace(year=today.year - years)
    except ValueError:
        return today.replace(
            year=today.year - years,
            month=2,
            day=28,
        )


class Command(BaseCommand):
    help = (
        "Crea o actualiza los datos demo de accounts de forma idempotente. "
        "Solo puede ejecutarse con DEBUG=True."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "seed_demo solo puede ejecutarse cuando DEBUG=True."
            )

        groups = self._upsert_groups()
        terms_versions = self._upsert_terms_versions()
        users = self._upsert_demo_users(groups)
        self._upsert_terms_acceptances(users, terms_versions)

        self.stdout.write(
            self.style.SUCCESS(
                "Seed demo de accounts completado sin duplicados."
            )
        )
        self.stdout.write(
            (
                f"Grupos: {Group.objects.count()} | "
                f"Usuarios demo gestionados: {len(users)} | "
                f"Versiones de términos: {TermsVersion.objects.count()} | "
                f"Aceptaciones: {TermsAcceptance.objects.count()}"
            )
        )

    def _upsert_groups(self) -> dict[str, Group]:
        groups = {}

        for name in ("CLIENTE", "VENDEDOR", "ADMINISTRADOR"):
            group, _ = Group.objects.update_or_create(
                name=name,
                defaults={},
            )
            groups[name] = group

        return groups

    def _upsert_terms_versions(self) -> dict[str, TermsVersion]:
        effective_at = timezone.now() - timedelta(days=30)

        terms, _ = TermsVersion.objects.update_or_create(
            kind=TermsVersion.Kind.TERMS,
            version="1.0",
            defaults={
                "title": "Términos académicos del Taller #3",
                "content": (
                    "Condiciones de uso de la simulación académica "
                    "Lotería Binaria."
                ),
                "effective_at": effective_at,
                "is_active": True,
            },
        )

        privacy, _ = TermsVersion.objects.update_or_create(
            kind=TermsVersion.Kind.PRIVACY,
            version="1.0",
            defaults={
                "title": "Política académica de privacidad",
                "content": (
                    "Tratamiento académico de datos para la demostración "
                    "del Taller #3."
                ),
                "effective_at": effective_at,
                "is_active": True,
            },
        )

        return {
            "terms": terms,
            "privacy": privacy,
        }

    def _upsert_demo_users(
        self,
        groups: dict[str, Group],
    ) -> dict[str, object]:
        User = get_user_model()

        demo_definitions = (
            {
                "key": "client",
                "username": "cliente_demo",
                "defaults": {
                    "email": "cliente.demo@example.test",
                    "document": "DEMO-CLIENTE-001",
                    "phone": "0990000001",
                    "birth_date": years_ago(25),
                    "first_name": "Cliente",
                    "last_name": "Demo",
                    "status": User.Status.ACTIVE,
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                },
                "group_names": ("CLIENTE",),
            },
            {
                "key": "vendor",
                "username": "vendedor_demo",
                "defaults": {
                    "email": "vendedor.demo@example.test",
                    "document": "DEMO-VENDEDOR-001",
                    "phone": "0990000002",
                    "birth_date": years_ago(30),
                    "first_name": "Vendedor",
                    "last_name": "Demo",
                    "status": User.Status.ACTIVE,
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                },
                "group_names": ("VENDEDOR",),
            },
            {
                "key": "multirole",
                "username": "multirole_demo",
                "defaults": {
                    "email": "multirole.demo@example.test",
                    "document": "DEMO-MULTIROL-001",
                    "phone": "0990000003",
                    "birth_date": years_ago(28),
                    "first_name": "Multirrol",
                    "last_name": "Demo",
                    "status": User.Status.ACTIVE,
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                },
                "group_names": ("CLIENTE", "VENDEDOR"),
            },
            {
                "key": "admin",
                "username": "admin_demo",
                "defaults": {
                    "email": "admin.demo@example.test",
                    "document": "DEMO-ADMIN-001",
                    "phone": "0990000004",
                    "birth_date": years_ago(35),
                    "first_name": "Administrador",
                    "last_name": "Demo",
                    "status": User.Status.ACTIVE,
                    "is_active": True,
                    "is_staff": True,
                    "is_superuser": True,
                },
                "group_names": ("ADMINISTRADOR",),
            },
        )

        users = {}

        for definition in demo_definitions:
            user, created = User.objects.update_or_create(
                username=definition["username"],
                defaults=definition["defaults"],
            )

            if created or not user.check_password(DEMO_PASSWORD):
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=("password",))

            user.groups.set(
                groups[name]
                for name in definition["group_names"]
            )

            users[definition["key"]] = user

        return users

    def _upsert_terms_acceptances(
        self,
        users: dict[str, object],
        terms_versions: dict[str, TermsVersion],
    ) -> None:
        for user in users.values():
            for terms_version in terms_versions.values():
                TermsAcceptance.objects.update_or_create(
                    user=user,
                    terms_version=terms_version,
                    defaults={
                        "ip_address": "127.0.0.1",
                    },
                )