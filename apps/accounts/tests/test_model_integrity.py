from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.accounts.models import TermsAcceptance

from .factories import create_terms_versions, create_user


class AccountModelIntegrityTests(TestCase):
    def test_user_identifiers_are_normalized_on_direct_orm_save(self):
        user = create_user(
            username="  Mixed_User  ",
            email="  MIXED@EXAMPLE.TEST  ",
            document="  ec-001  ",
        )

        self.assertEqual(user.username, "mixed_user")
        self.assertEqual(user.email, "mixed@example.test")
        self.assertEqual(user.document, "EC-001")

    def test_accepted_legal_version_content_is_immutable(self):
        terms, _ = create_terms_versions()
        user = create_user()
        TermsAcceptance.objects.create(user=user, terms_version=terms)

        terms.title = "Título alterado"
        with self.assertRaisesMessage(
            ValidationError,
            "conserva su contenido histórico",
        ):
            terms.save()
        with self.assertRaisesMessage(
            ValidationError,
            "conserva su contenido histórico",
        ):
            type(terms).objects.filter(pk=terms.pk).update(
                title="Título alterado por lote"
            )

        terms.refresh_from_db()
        self.assertEqual(terms.title, "Términos de prueba")

    def test_accepted_legal_version_can_be_deactivated_without_rewriting_it(self):
        terms, _ = create_terms_versions()
        user = create_user()
        TermsAcceptance.objects.create(user=user, terms_version=terms)

        terms.is_active = False
        terms.save(update_fields=("is_active",))
        terms.refresh_from_db()

        self.assertFalse(terms.is_active)

    def test_acceptance_cannot_be_edited_or_deleted(self):
        terms, _ = create_terms_versions()
        user = create_user()
        acceptance = TermsAcceptance.objects.create(
            user=user,
            terms_version=terms,
            ip_address="192.0.2.10",
        )

        acceptance.ip_address = "192.0.2.20"
        with self.assertRaisesMessage(
            ValidationError,
            "no se editan",
        ):
            acceptance.save()
        with self.assertRaisesMessage(
            ValidationError,
            "no se editan",
        ):
            TermsAcceptance.objects.filter(pk=acceptance.pk).update(
                ip_address="192.0.2.30"
            )
        with self.assertRaisesMessage(
            ValidationError,
            "no se eliminan",
        ):
            acceptance.delete()
        with self.assertRaisesMessage(
            ValidationError,
            "no se eliminan",
        ):
            TermsAcceptance.objects.filter(pk=acceptance.pk).delete()

        self.assertTrue(TermsAcceptance.objects.filter(pk=acceptance.pk).exists())
