from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import TermsAcceptance, TermsVersion, User
from apps.accounts.roles import CLIENT

from .factories import VALID_PASSWORD, adult_birth_date, create_terms_versions


class RegistrationViewTests(TestCase):
    def setUp(self):
        create_terms_versions()
        self.url = reverse("accounts:register")

    def payload(self, **overrides):
        data = {
            "username": "cliente_nuevo",
            "email": "CLIENTE@EXAMPLE.TEST",
            "document": " DOC-001 ",
            "phone": " 0999999999 ",
            "birth_date": adult_birth_date().isoformat(),
            "first_name": "Cliente",
            "last_name": "Nuevo",
            "password1": VALID_PASSWORD,
            "password2": VALID_PASSWORD,
            "accept_terms": "on",
            "accept_privacy": "on",
        }
        data.update(overrides)
        return data

    def test_registration_creates_normalized_client_and_acceptances(self):
        response = self.client.post(self.url, self.payload())

        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(username="cliente_nuevo")
        self.assertEqual(user.email, "cliente@example.test")
        self.assertEqual(user.document, "DOC-001")
        self.assertEqual(user.phone, "0999999999")
        self.assertTrue(user.check_password(VALID_PASSWORD))
        self.assertTrue(user.groups.filter(name=CLIENT).exists())
        self.assertEqual(TermsAcceptance.objects.filter(user=user).count(), 2)

    def test_minor_is_rejected(self):
        birth_date = timezone.localdate() - timedelta(days=365 * 17)
        response = self.client.post(
            self.url,
            self.payload(birth_date=birth_date.isoformat()),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Debes ser mayor de edad")
        self.assertFalse(User.objects.filter(username="cliente_nuevo").exists())

    def test_case_insensitive_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existente",
            email="cliente@example.test",
            document="DOC-EXISTENTE",
            birth_date=adult_birth_date(),
            password=VALID_PASSWORD,
        )
        response = self.client.post(self.url, self.payload())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe una cuenta con este correo")
        self.assertEqual(User.objects.filter(email="cliente@example.test").count(), 1)

    def test_registration_closes_when_legal_version_is_missing(self):
        TermsVersion.objects.filter(kind=TermsVersion.Kind.PRIVACY).update(
            is_active=False
        )
        response = self.client.post(self.url, self.payload())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "registro está temporalmente cerrado")
        self.assertFalse(User.objects.filter(username="cliente_nuevo").exists())


    def test_registration_rejects_legal_version_superseded_during_save(self):
        from apps.accounts.forms import RegistrationForm

        form = RegistrationForm(data=self.payload())
        self.assertTrue(form.is_valid(), form.errors.as_json())
        TermsVersion.objects.create(
            kind=TermsVersion.Kind.TERMS,
            version="test-2",
            title="Términos más recientes",
            content="Nueva versión académica.",
            effective_at=timezone.now(),
            is_active=True,
        )

        with self.assertRaisesMessage(
            ValidationError,
            "dejó de ser la vigente",
        ):
            form.save(ip_address="127.0.0.1")
        self.assertFalse(User.objects.filter(username="cliente_nuevo").exists())

    def test_registration_post_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(self.url, self.payload())

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="cliente_nuevo").exists())

    def test_registration_reuses_existing_client_group_without_duplicates(self):
        # El seed puede haber creado el grupo antes del primer registro.
        Group.objects.get_or_create(name=CLIENT)
        response = self.client.post(self.url, self.payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.filter(username="cliente_nuevo").count(), 1)

    def test_case_insensitive_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username="cliente_nuevo",
            email="otro@example.test",
            document="DOC-OTRO",
            birth_date=adult_birth_date(),
            password=VALID_PASSWORD,
        )

        response = self.client.post(
            self.url,
            self.payload(username="CLIENTE_NUEVO"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe una cuenta con este usuario")
        self.assertEqual(
            User.objects.filter(username__iexact="cliente_nuevo").count(),
            1,
        )

    def test_case_insensitive_duplicate_document_is_rejected(self):
        User.objects.create_user(
            username="otro_usuario",
            email="otro@example.test",
            document="DOC-001",
            birth_date=adult_birth_date(),
            password=VALID_PASSWORD,
        )

        response = self.client.post(
            self.url,
            self.payload(document="doc-001"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe una cuenta con este documento")
        self.assertEqual(User.objects.filter(document="DOC-001").count(), 1)

    def test_invalid_field_is_rendered_with_bootstrap_and_aria_state(self):
        response = self.client.post(
            self.url,
            self.payload(email="correo-invalido"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="form-control is-invalid"')
        self.assertContains(response, 'aria-invalid="true"')

