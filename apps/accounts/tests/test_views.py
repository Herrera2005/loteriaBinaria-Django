from __future__ import annotations

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.models import TermsAcceptance, User
from apps.accounts.roles import ADMINISTRATOR, CLIENT

from .factories import (
    VALID_PASSWORD,
    adult_birth_date,
    create_terms_versions,
    create_user,
)


class UserCrudAccessTests(TestCase):
    def setUp(self):
        self.admin_user = create_user(
            username="admin_crud",
            email="admin@example.test",
            document="ADMIN-CRUD",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )

    def activate_admin_mode(self):
        self.client.force_login(self.admin_user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("accounts:user_list"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:user_list')}",
        )

    def test_non_staff_user_receives_403(self):
        user = create_user(
            username="admin_sin_staff",
            email="sin-staff@example.test",
            document="SIN-STAFF",
            roles=(ADMINISTRATOR,),
            is_staff=False,
        )
        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

        response = self.client.get(reverse("accounts:user_list"))

        self.assertEqual(response.status_code, 403)

    def test_staff_without_active_administrator_mode_receives_403(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("accounts:user_list"))

        self.assertEqual(response.status_code, 403)

    def test_administrator_mode_can_access_all_crud_pages(self):
        managed_user = create_user(
            username="usuario_objetivo",
            email="objetivo@example.test",
            document="OBJ-001",
        )
        self.activate_admin_mode()

        urls = (
            reverse("accounts:user_list"),
            reverse("accounts:user_create"),
            reverse("accounts:user_detail", args=(managed_user.pk,)),
            reverse("accounts:user_update", args=(managed_user.pk,)),
            reverse("accounts:user_delete", args=(managed_user.pk,)),
        )

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class UserCrudTests(TestCase):
    def setUp(self):
        self.admin_user = create_user(
            username="admin_crud",
            email="admin@example.test",
            document="ADMIN-CRUD",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        self.client.force_login(self.admin_user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

    def creation_payload(self, **overrides):
        data = {
            "username": "nuevo_usuario",
            "email": "nuevo@example.test",
            "document": "NUEVO-001",
            "phone": "0999999999",
            "birth_date": adult_birth_date().isoformat(),
            "first_name": "Nuevo",
            "last_name": "Usuario",
            "status": User.Status.ACTIVE,
            "is_active": "on",
            "is_staff": "",
            "is_superuser": "",
            "groups": [],
            "user_permissions": [],
            "password1": VALID_PASSWORD,
            "password2": VALID_PASSWORD,
        }
        data.update(overrides)
        return data

    def change_payload(self, user, **overrides):
        data = {
            "username": user.username,
            "password": user.password,
            "email": user.email,
            "document": user.document,
            "phone": user.phone,
            "birth_date": user.birth_date.isoformat(),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "status": user.status,
            "is_active": "on" if user.is_active else "",
            "is_staff": "on" if user.is_staff else "",
            "is_superuser": "on" if user.is_superuser else "",
            "groups": list(user.groups.values_list("pk", flat=True)),
            "user_permissions": list(
                user.user_permissions.values_list("pk", flat=True)
            ),
        }
        data.update(overrides)
        return data

    def test_list_supports_search(self):
        create_user(
            username="cliente_busqueda",
            email="busqueda@example.test",
            document="BUS-001",
        )

        response = self.client.get(
            reverse("accounts:user_list"),
            {"q": "BUS-001"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cliente_busqueda")
        self.assertNotContains(response, "No se encontraron usuarios")

    def test_list_is_paginated(self):
        for index in range(16):
            create_user(
                username=f"usuario_{index:02d}",
                email=f"usuario_{index:02d}@example.test",
                document=f"PAG-{index:02d}",
            )

        response = self.client.get(reverse("accounts:user_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["users"]), 15)

    def test_create_hashes_password_and_redirects_to_detail(self):
        response = self.client.post(
            reverse("accounts:user_create"),
            self.creation_payload(),
        )

        user = User.objects.get(username="nuevo_usuario")
        self.assertRedirects(
            response,
            reverse("accounts:user_detail", args=(user.pk,)),
        )
        self.assertTrue(user.check_password(VALID_PASSWORD))
        self.assertNotEqual(user.password, VALID_PASSWORD)

    def test_update_changes_allowed_fields_and_preserves_password(self):
        user = create_user(
            username="editable",
            email="editable@example.test",
            document="EDIT-001",
        )
        original_password = user.password

        response = self.client.post(
            reverse("accounts:user_update", args=(user.pk,)),
            self.change_payload(
                user,
                first_name="Actualizado",
                email="actualizado@example.test",
            ),
        )

        self.assertRedirects(
            response,
            reverse("accounts:user_detail", args=(user.pk,)),
        )
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Actualizado")
        self.assertEqual(user.email, "actualizado@example.test")
        self.assertEqual(user.password, original_password)

    def test_delete_physically_removes_user_without_history(self):
        user = create_user(
            username="sin_historia",
            email="sin-historia@example.test",
            document="SIN-HIST",
        )

        response = self.client.post(
            reverse("accounts:user_delete", args=(user.pk,)),
        )

        self.assertRedirects(response, reverse("accounts:user_list"))
        self.assertFalse(User.objects.filter(pk=user.pk).exists())

    def test_delete_deactivates_user_with_terms_history(self):
        terms, _ = create_terms_versions()
        user = create_user(
            username="con_historia",
            email="con-historia@example.test",
            document="CON-HIST",
            roles=(CLIENT,),
        )
        acceptance = TermsAcceptance.objects.create(
            user=user,
            terms_version=terms,
            ip_address="127.0.0.1",
        )

        response = self.client.post(
            reverse("accounts:user_delete", args=(user.pk,)),
        )

        self.assertRedirects(response, reverse("accounts:user_list"))
        user.refresh_from_db()
        self.assertEqual(user.status, User.Status.DISABLED)
        self.assertFalse(user.is_active)
        self.assertTrue(
            TermsAcceptance.objects.filter(pk=acceptance.pk).exists()
        )

    def test_cannot_delete_or_deactivate_current_user(self):
        response = self.client.post(
            reverse("accounts:user_delete", args=(self.admin_user.pk,)),
        )

        self.assertRedirects(
            response,
            reverse(
                "accounts:user_detail",
                args=(self.admin_user.pk,),
            ),
        )
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)

    def test_missing_user_delete_returns_404(self):
        response = self.client.get(
            reverse("accounts:user_delete", args=(999999,))
        )

        self.assertEqual(response.status_code, 404)

    def test_crud_post_requires_csrf(self):
        from django.test import Client

        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.admin_user)
        session = csrf_client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

        response = csrf_client.post(
            reverse("accounts:user_create"),
            self.creation_payload(),
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            User.objects.filter(username="nuevo_usuario").exists()
        )
