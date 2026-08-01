from datetime import date
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.accounts.models import TermsAcceptance, TermsVersion
from apps.accounts.roles import ROLE_CODES


class SeedCommandTests(TestCase):
    def test_seed_baseline_is_idempotent(self):
        call_command("seed_baseline", stdout=StringIO())
        call_command("seed_baseline", stdout=StringIO())

        self.assertEqual(Group.objects.filter(name__in=ROLE_CODES).count(), 3)
        self.assertEqual(TermsVersion.objects.count(), 2)

    def test_seed_baseline_does_not_mutate_an_accepted_legal_version(self):
        call_command("seed_baseline", stdout=StringIO())
        terms = TermsVersion.objects.get(
            kind=TermsVersion.Kind.TERMS,
            version="1.1.0",
        )
        terms.title = "Título histórico conservado"
        terms.save(update_fields=("title",))

        User = get_user_model()
        user = User.objects.create_user(
            username="legal_history",
            email="legal.history@example.test",
            document="LEGAL-HISTORY-001",
            birth_date=date(2000, 1, 1),
            password="AcademicPass#2026",
        )
        TermsAcceptance.objects.create(user=user, terms_version=terms)

        call_command("seed_baseline", stdout=StringIO())

        terms.refresh_from_db()
        self.assertEqual(terms.title, "Título histórico conservado")

    @override_settings(DEBUG=True, DEMO_PASSWORD="")
    def test_seed_demo_requires_password_from_environment(self):
        with self.assertRaisesMessage(CommandError, "DJANGO_DEMO_PASSWORD"):
            call_command("seed_demo", stdout=StringIO())

    @override_settings(DEBUG=False, DEMO_PASSWORD="AcademicPass#2026")
    def test_seed_demo_is_forbidden_outside_debug(self):
        with self.assertRaisesMessage(CommandError, "DEBUG=True"):
            call_command("seed_demo", stdout=StringIO())

    @override_settings(DEBUG=True, DEMO_PASSWORD="AcademicPass#2026")
    def test_seed_demo_is_idempotent_and_does_not_duplicate_acceptances(self):
        call_command("seed_demo", stdout=StringIO())
        call_command("seed_demo", stdout=StringIO())

        User = get_user_model()
        self.assertEqual(User.objects.filter(username__endswith="_demo").count(), 4)
        self.assertEqual(TermsAcceptance.objects.count(), 8)

    @override_settings(DEBUG=True, DEMO_PASSWORD="AcademicPass#2026")
    def test_seed_demo_preserves_an_existing_acceptance_ip(self):
        call_command("seed_baseline", stdout=StringIO())
        User = get_user_model()
        user = User.objects.create_user(
            username="cliente_demo",
            email="preexistente@example.test",
            document="PREEXISTENTE-001",
            birth_date=date(2000, 1, 1),
            password="AcademicPass#2026",
        )
        terms = TermsVersion.objects.get(kind=TermsVersion.Kind.TERMS)
        acceptance = TermsAcceptance.objects.create(
            user=user,
            terms_version=terms,
            ip_address="192.0.2.55",
        )

        call_command("seed_demo", stdout=StringIO())

        acceptance.refresh_from_db()
        self.assertEqual(acceptance.ip_address, "192.0.2.55")

