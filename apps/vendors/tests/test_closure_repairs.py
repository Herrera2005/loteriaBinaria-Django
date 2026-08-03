from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import ADMINISTRATOR, CLIENT, VENDOR
from apps.accounts.tests.factories import create_user
from apps.vendors.forms import VendorProfileForm
from apps.vendors.models import ConversionAssignment, ConversionRequest, VendorProfile


class VendorClosureRegressionTests(TestCase):
    def test_vendor_detail_paginates_assignments(self):
        admin = create_user(
            username="vendor_page_admin",
            email="vendor-page-admin@example.test",
            document="VENDOR-PAGE-ADMIN",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        vendor_user = create_user(
            username="vendor_page_user",
            email="vendor-page-user@example.test",
            document="VENDOR-PAGE-USER",
            roles=(VENDOR,),
        )
        profile = VendorProfile.objects.create(
            user=vendor_user,
            status=VendorProfile.Status.ACTIVE,
        )
        for index in range(16):
            client = create_user(
                username=f"vendor_page_client_{index}",
                email=f"vendor-page-client-{index}@example.test",
                document=f"VENDOR-PAGE-CLIENT-{index}",
                roles=(CLIENT,),
            )
            request = ConversionRequest.objects.create(
                client=client,
                amount_minor=100,
                expires_at=timezone.now() + timedelta(minutes=5),
            )
            ConversionAssignment.objects.create(
                request=request,
                vendor=profile,
            )

        self.client.force_login(admin)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()
        response = self.client.get(
            reverse("vendors:vendorprofile_detail", args=(profile.pk,))
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.context["assignments_page"].object_list),
            15,
        )
        self.assertTrue(response.context["assignments_page"].has_next())

    def test_model_and_form_share_vendor_account_validation(self):
        user = create_user(
            username="vendor_invalid_shared",
            email="vendor-invalid-shared@example.test",
            document="VENDOR-INVALID-SHARED",
            roles=(CLIENT,),
        )
        profile = VendorProfile(
            user=user,
            status=VendorProfile.Status.ACTIVE,
        )
        with self.assertRaises(ValidationError) as model_error:
            profile.full_clean()
        self.assertIn("user", model_error.exception.message_dict)

        form = VendorProfileForm(
            data={
                "user": user.pk,
                "status": VendorProfile.Status.ACTIVE,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue("user" in form.errors or "status" in form.errors)
