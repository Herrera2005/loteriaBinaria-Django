from __future__ import annotations

from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from apps.accounts.forms import (
    ProfileUpdateForm,
    TermsVersionForm,
    UserAdminChangeForm,
    UserAdminCreationForm,
)
from apps.accounts.models import TermsAcceptance, TermsVersion, User
from apps.accounts.services import age_cutoff


VALID_PASSWORD = "ClaveSegura-T3-2026!"


def adult_birth_date() -> date:
    cutoff = age_cutoff()
    return cutoff.replace(year=cutoff.year - 5)


def user_form_data(**overrides):
    data = {
        "username": " Usuario_Admin ",
        "email": " USUARIO@EXAMPLE.TEST ",
        "document": " ec-001 ",
        "phone": " 0999999999 ",
        "birth_date": adult_birth_date(),
        "first_name": "Usuario",
        "last_name": "Prueba",
        "status": User.Status.ACTIVE,
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
        "groups": [],
        "user_permissions": [],
        "password1": VALID_PASSWORD,
        "password2": VALID_PASSWORD,
    }
    data.update(overrides)
    return data


class UserAdminCreationFormTests(TestCase):
    def test_valid_form_normalizes_identity_and_hashes_password(self):
        form = UserAdminCreationForm(data=user_form_data())

        self.assertTrue(form.is_valid(), form.errors.as_json())
        user = form.save()

        self.assertEqual(user.username, "usuario_admin")
        self.assertEqual(user.email, "usuario@example.test")
        self.assertEqual(user.document, "EC-001")
        self.assertEqual(user.phone, "0999999999")
        self.assertNotEqual(user.password, VALID_PASSWORD)
        self.assertTrue(user.check_password(VALID_PASSWORD))

    def test_minor_is_rejected(self):
        minor_birth_date = timezone.localdate() - timedelta(days=365 * 17)
        form = UserAdminCreationForm(
            data=user_form_data(birth_date=minor_birth_date)
        )

        self.assertFalse(form.is_valid())
        self.assertIn("birth_date", form.errors)
        self.assertIn("mayor de edad", form.errors["birth_date"][0])

    def test_email_is_unique_case_insensitively(self):
        User.objects.create_user(
            username="existente",
            email="usuario@example.test",
            document="OTRO-001",
            birth_date=adult_birth_date(),
            password=VALID_PASSWORD,
        )
        form = UserAdminCreationForm(data=user_form_data())

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn("Ya existe", form.errors["email"][0])

    def test_document_is_unique_case_insensitively(self):
        User.objects.create_user(
            username="existente",
            email="otro@example.test",
            document="EC-001",
            birth_date=adult_birth_date(),
            password=VALID_PASSWORD,
        )
        form = UserAdminCreationForm(
            data=user_form_data(email="nuevo@example.test")
        )

        self.assertFalse(form.is_valid())
        self.assertIn("document", form.errors)
        self.assertIn("Ya existe", form.errors["document"][0])

    def test_inactive_status_cannot_keep_access_enabled(self):
        form = UserAdminCreationForm(
            data=user_form_data(
                status=User.Status.SUSPENDED,
                is_active=True,
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("is_active", form.errors)

    def test_password_confirmation_is_required(self):
        form = UserAdminCreationForm(
            data=user_form_data(password2="otra-clave")
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


class UserAdminChangeFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="usuario_actual",
            email="actual@example.test",
            document="ACT-001",
            phone="",
            birth_date=adult_birth_date(),
            password=VALID_PASSWORD,
            status=User.Status.ACTIVE,
            is_active=True,
        )

    def change_data(self, **overrides):
        data = {
            "username": self.user.username,
            "password": self.user.password,
            "email": self.user.email,
            "document": self.user.document,
            "phone": self.user.phone,
            "birth_date": self.user.birth_date,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "status": self.user.status,
            "is_active": self.user.is_active,
            "is_staff": self.user.is_staff,
            "is_superuser": self.user.is_superuser,
            "groups": [],
            "user_permissions": [],
        }
        data.update(overrides)
        return data

    def test_current_identity_values_are_not_treated_as_duplicates(self):
        form = UserAdminChangeForm(
            instance=self.user,
            data=self.change_data(
                username=" USUARIO_ACTUAL ",
                email=" ACTUAL@EXAMPLE.TEST ",
                document=" act-001 ",
            ),
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_change_preserves_password_hash(self):
        old_password_hash = self.user.password
        form = UserAdminChangeForm(
            instance=self.user,
            data=self.change_data(
                first_name="Nombre actualizado",
            ),
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        user = form.save()

        self.assertEqual(user.password, old_password_hash)
        self.assertTrue(user.check_password(VALID_PASSWORD))
        self.assertEqual(user.first_name, "Nombre actualizado")

    def test_change_rejects_identity_owned_by_another_user(self):
        User.objects.create_user(
            username="otro",
            email="otro@example.test",
            document="OTRO-001",
            birth_date=adult_birth_date(),
            password=VALID_PASSWORD,
        )
        form = UserAdminChangeForm(
            instance=self.user,
            data=self.change_data(email="OTRO@EXAMPLE.TEST"),
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class TermsVersionFormTests(TestCase):
    def setUp(self):
        self.terms = TermsVersion.objects.create(
            kind=TermsVersion.Kind.TERMS,
            version="1.0",
            title="Términos académicos",
            content="Contenido legal académico.",
            effective_at=(
                timezone.now() - timedelta(days=1)
            ).replace(microsecond=0),
            is_active=True,
        )
        self.user = User.objects.create_user(
            username="cliente",
            email="cliente@example.test",
            document="CLI-001",
            birth_date=adult_birth_date(),
            password=VALID_PASSWORD,
        )

    def form_data(self, **overrides):
        effective_at_local = timezone.localtime(
            self.terms.effective_at
        ).replace(microsecond=0)

        data = {
            "kind": self.terms.kind,
            "version": self.terms.version,
            "title": self.terms.title,
            "content": self.terms.content,
            "effective_at": effective_at_local.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
            "is_active": self.terms.is_active,
        }
        data.update(overrides)
        return data
    
    def test_unaccepted_version_can_be_edited(self):
        form = TermsVersionForm(
            instance=self.terms,
            data=self.form_data(title="Título actualizado"),
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        terms = form.save()
        self.assertEqual(terms.title, "Título actualizado")

    def test_accepted_version_rejects_historical_content_change(self):
        TermsAcceptance.objects.create(
            user=self.user,
            terms_version=self.terms,
            ip_address="127.0.0.1",
        )
        form = TermsVersionForm(
            instance=self.terms,
            data=self.form_data(content="Contenido reemplazado."),
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            "conserva su contenido histórico",
            form.non_field_errors()[0],
        )

    def test_deactivating_accepted_version_preserves_acceptance(self):
        acceptance = TermsAcceptance.objects.create(
            user=self.user,
            terms_version=self.terms,
            ip_address="127.0.0.1",
        )

        form = TermsVersionForm(
            instance=self.terms,
            data=self.form_data(is_active=False),
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())

        updated_terms = form.save()

        self.assertFalse(updated_terms.is_active)
        self.assertTrue(
            TermsAcceptance.objects.filter(pk=acceptance.pk).exists()
        )

        acceptance.refresh_from_db()
        self.assertEqual(acceptance.terms_version_id, updated_terms.pk)

    def test_accepted_version_rejects_effective_date_change(self):
        TermsAcceptance.objects.create(
            user=self.user,
            terms_version=self.terms,
        )

        changed_effective_at = timezone.localtime(
            self.terms.effective_at + timedelta(days=1)
        ).replace(microsecond=0).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )

        form = TermsVersionForm(
            instance=self.terms,
            data=self.form_data(
                effective_at=changed_effective_at,
            ),
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            "vigente desde",
            form.non_field_errors()[0].lower(),
        )

    def test_accepted_version_can_be_deactivated(self):
        TermsAcceptance.objects.create(
            user=self.user,
            terms_version=self.terms,
        )
        form = TermsVersionForm(
            instance=self.terms,
            data=self.form_data(is_active=False),
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        terms = form.save()
        self.assertFalse(terms.is_active)

    def test_empty_legal_content_is_rejected(self):
        form = TermsVersionForm(
            data={
                "kind": TermsVersion.Kind.PRIVACY,
                "version": "1.0",
                "title": "Privacidad",
                "content": "   ",
                "effective_at": timezone.now().strftime(
                    "%Y-%m-%dT%H:%M:%S"
                ),
                "is_active": True,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)



class ProfileUpdateFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="perfil_actual",
            email="perfil@example.test",
            document="PERFIL-001",
            phone="0991111111",
            birth_date=adult_birth_date(),
            first_name="Perfil",
            last_name="Actual",
            password=VALID_PASSWORD,
        )

    def payload(self, **overrides):
        data = {
            "username": self.user.username,
            "email": self.user.email,
            "document": self.user.document,
            "phone": self.user.phone,
            "birth_date": self.user.birth_date,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        data.update(overrides)
        return data

    def test_profile_form_updates_and_normalizes_personal_data(self):
        form = ProfileUpdateForm(
            instance=self.user,
            data=self.payload(
                username=" PERFIL_NUEVO ",
                email=" NUEVO@EXAMPLE.TEST ",
                document=" perfil-002 ",
                phone=" 0992222222 ",
                first_name="Nombre",
                last_name="Actualizado",
            ),
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        user = form.save()

        self.assertEqual(user.username, "perfil_nuevo")
        self.assertEqual(user.email, "nuevo@example.test")
        self.assertEqual(user.document, "PERFIL-002")
        self.assertEqual(user.phone, "0992222222")
        self.assertEqual(user.first_name, "Nombre")
        self.assertEqual(user.last_name, "Actualizado")

    def test_profile_form_rejects_identity_owned_by_another_user(self):
        User.objects.create_user(
            username="otra_cuenta",
            email="otra@example.test",
            document="OTRA-001",
            birth_date=adult_birth_date(),
            password=VALID_PASSWORD,
        )

        form = ProfileUpdateForm(
            instance=self.user,
            data=self.payload(email="OTRA@EXAMPLE.TEST"),
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_profile_form_does_not_expose_privilege_fields(self):
        form = ProfileUpdateForm(instance=self.user)

        self.assertNotIn("status", form.fields)
        self.assertNotIn("is_active", form.fields)
        self.assertNotIn("is_staff", form.fields)
        self.assertNotIn("is_superuser", form.fields)
        self.assertNotIn("groups", form.fields)
        self.assertNotIn("user_permissions", form.fields)
        self.assertNotIn("password", form.fields)
