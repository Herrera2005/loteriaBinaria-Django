"""Pruebas de acceso y CRUD visual del módulo vendors."""

from __future__ import annotations

from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import ADMINISTRATOR, CLIENT, VENDOR
from apps.accounts.tests.factories import create_user
from apps.vendors.models import (
    ConversionAssignment,
    ConversionRequest,
    VendorProfile,
)



def create_vendor_user(
    *,
    username: str,
    email: str,
    document: str,
):
    return create_user(
        username=username,
        email=email,
        document=document,
        roles=(VENDOR,),
    )


def create_vendor_profile(
    *,
    username: str = "vendedor_crud",
    email: str = "vendedor-crud@example.test",
    document: str = "VEND-CRUD",
    status: str = VendorProfile.Status.ACTIVE,
):
    user = create_vendor_user(
        username=username,
        email=email,
        document=document,
    )
    profile = VendorProfile(user=user, status=status)
    profile.full_clean()
    profile.save()
    return profile


def create_conversion_request(*, client=None, status=None):
    client = client or create_user(
        username="cliente_solicitud",
        email="cliente-solicitud@example.test",
        document="CLI-SOL-001",
        roles=(CLIENT,),
    )
    return ConversionRequest.objects.create(
        client=client,
        amount_minor=1000,
        status=status or ConversionRequest.Status.PENDING,
        expires_at=timezone.now() + timedelta(minutes=10),
    )


class VendorCrudAccessTests(TestCase):
    def setUp(self):
        self.admin_user = create_user(
            username="admin_vendors",
            email="admin-vendors@example.test",
            document="ADMIN-VEND",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )

    def activate_admin_mode(self):
        self.client.force_login(self.admin_user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("vendors:vendorprofile_list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_authenticated_user_without_admin_mode_receives_403(self):
        user = create_user(
            username="cliente_sin_permiso",
            email="cliente-sin-permiso@example.test",
            document="CLI-SIN-PERM",
            roles=(CLIENT,),
        )
        self.client.force_login(user)

        response = self.client.get(reverse("vendors:vendorprofile_list"))

        self.assertEqual(response.status_code, 403)

    def test_administrator_can_access_all_get_views(self):
        profile = create_vendor_profile()
        self.activate_admin_mode()

        urls = (
            reverse("vendors:vendorprofile_list"),
            reverse("vendors:vendorprofile_create"),
            reverse("vendors:vendorprofile_detail", args=(profile.pk,)),
            reverse("vendors:vendorprofile_update", args=(profile.pk,)),
            reverse("vendors:vendorprofile_delete", args=(profile.pk,)),
            reverse("vendors:conversionrequest_list"),
        )

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class VendorProfileCrudTests(TestCase):
    def setUp(self):
        self.admin_user = create_user(
            username="admin_vendors",
            email="admin-vendors@example.test",
            document="ADMIN-VEND",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        self.client.force_login(self.admin_user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

    def test_list_filters_by_status(self):
        active = create_vendor_profile(
            username="vendedor_activo",
            email="vendedor-activo@example.test",
            document="VEND-ACT",
            status=VendorProfile.Status.ACTIVE,
        )
        suspended = create_vendor_profile(
            username="vendedor_suspendido",
            email="vendedor-suspendido@example.test",
            document="VEND-SUSP",
            status=VendorProfile.Status.SUSPENDED,
        )

        response = self.client.get(
            reverse("vendors:vendorprofile_list"),
            {"status": VendorProfile.Status.ACTIVE},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, active.user.username)
        self.assertNotContains(response, suspended.user.username)

    def test_list_has_pagination(self):
        for index in range(16):
            create_vendor_profile(
                username=f"vendedor_{index:02d}",
                email=f"vendedor_{index:02d}@example.test",
                document=f"VEND-{index:02d}",
            )

        response = self.client.get(reverse("vendors:vendorprofile_list"))

        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["vendor_profiles"]), 15)

    def test_create_vendor_profile(self):
        user = create_vendor_user(
            username="vendedor_nuevo",
            email="vendedor-nuevo@example.test",
            document="VEND-NUEVO",
        )

        response = self.client.post(
            reverse("vendors:vendorprofile_create"),
            {
                "user": user.pk,
                "status": VendorProfile.Status.ACTIVE,
            },
        )

        profile = VendorProfile.objects.get(user=user)
        self.assertRedirects(
            response,
            reverse(
                "vendors:vendorprofile_detail",
                args=(profile.pk,),
            ),
        )
        self.assertEqual(profile.status, VendorProfile.Status.ACTIVE)

    def test_update_changes_status_without_changing_user(self):
        profile = create_vendor_profile()
        original_user_id = profile.user_id

        response = self.client.post(
            reverse(
                "vendors:vendorprofile_update",
                args=(profile.pk,),
            ),
            {
                "user": profile.user_id,
                "status": VendorProfile.Status.SUSPENDED,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "vendors:vendorprofile_detail",
                args=(profile.pk,),
            ),
        )
        profile.refresh_from_db()
        self.assertEqual(profile.user_id, original_user_id)
        self.assertEqual(
            profile.status,
            VendorProfile.Status.SUSPENDED,
        )

    def test_delete_physically_removes_profile_without_history(self):
        profile = create_vendor_profile()
        user_id = profile.user_id

        response = self.client.post(
            reverse(
                "vendors:vendorprofile_delete",
                args=(profile.pk,),
            ),
        )

        self.assertRedirects(
            response,
            reverse("vendors:vendorprofile_list"),
        )
        self.assertFalse(
            VendorProfile.objects.filter(pk=profile.pk).exists()
        )
        self.assertTrue(
            profile.user.__class__.objects.filter(pk=user_id).exists()
        )

    def test_delete_deactivates_profile_with_assignment_history(self):
        profile = create_vendor_profile()
        conversion_request = create_conversion_request()
        assignment = ConversionAssignment.objects.create(
            request=conversion_request,
            vendor=profile,
        )

        response = self.client.post(
            reverse(
                "vendors:vendorprofile_delete",
                args=(profile.pk,),
            ),
        )

        self.assertRedirects(
            response,
            reverse("vendors:vendorprofile_list"),
        )
        profile.refresh_from_db()
        self.assertEqual(
            profile.status,
            VendorProfile.Status.DISABLED,
        )
        self.assertTrue(
            ConversionAssignment.objects.filter(
                pk=assignment.pk,
            ).exists()
        )

    def test_detail_renders_profile_not_request_list(self):
        profile = create_vendor_profile()

        response = self.client.get(
            reverse(
                "vendors:vendorprofile_detail",
                args=(profile.pk,),
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, profile.user.username)
        self.assertContains(response, "Datos del perfil")
        self.assertNotContains(response, "Solicitudes de conversión")

    def test_missing_profile_delete_returns_404(self):
        response = self.client.get(
            reverse("vendors:vendorprofile_delete", args=(999999,))
        )

        self.assertEqual(response.status_code, 404)

    def test_sensitive_post_requires_csrf(self):
        profile = create_vendor_profile()
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.admin_user)
        session = csrf_client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

        response = csrf_client.post(
            reverse(
                "vendors:vendorprofile_delete",
                args=(profile.pk,),
            ),
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            VendorProfile.objects.filter(pk=profile.pk).exists()
        )


class ConversionRequestReadOnlyViewTests(TestCase):
    def setUp(self):
        self.admin_user = create_user(
            username="admin_solicitudes",
            email="admin-solicitudes@example.test",
            document="ADMIN-SOL",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        self.client.force_login(self.admin_user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

    def test_request_list_is_visible_and_has_no_edit_actions(self):
        conversion_request = create_conversion_request()

        response = self.client.get(
            reverse("vendors:conversionrequest_list"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            str(conversion_request.operation_id),
        )
        self.assertNotContains(response, "Editar solicitud")
        self.assertNotContains(response, "Eliminar solicitud")

    def test_request_list_filters_by_status(self):
        pending = create_conversion_request(
            status=ConversionRequest.Status.PENDING,
        )
        completed_client = create_user(
            username="cliente_completado",
            email="cliente-completado@example.test",
            document="CLI-COMP",
            roles=(CLIENT,),
        )
        completed = create_conversion_request(
            client=completed_client,
            status=ConversionRequest.Status.COMPLETED_BY_PLATFORM,
        )

        response = self.client.get(
            reverse("vendors:conversionrequest_list"),
            {"status": ConversionRequest.Status.PENDING},
        )

        self.assertContains(response, str(pending.operation_id))
        self.assertNotContains(response, str(completed.operation_id))

    def test_request_list_rejects_post(self):
        response = self.client.post(
            reverse("vendors:conversionrequest_list"),
            {"status": ConversionRequest.Status.COMPLETED_BY_VENDOR},
        )

        self.assertEqual(response.status_code, 405)