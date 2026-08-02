from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from apps.accounts.admin import (
    CustomUserAdmin,
    TermsAcceptanceAdmin,
    TermsVersionAdmin,
)
from apps.accounts.models import TermsAcceptance, TermsVersion, User

from .factories import create_terms_versions, create_user


class ProtectedAdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.request = RequestFactory().get("/admin/")
        self.request.user = create_user(
            username="staff",
            email="staff@example.test",
            document="STAFF-001",
            is_staff=True,
            is_superuser=True,
        )

    def test_user_delete_is_disabled(self):
        model_admin = CustomUserAdmin(User, self.site)
        self.assertFalse(model_admin.has_delete_permission(self.request))

    def test_user_change_form_renders_birth_date_in_iso_format(self):
        model_admin = CustomUserAdmin(User, self.site)
        form_class = model_admin.get_form(
            self.request,
            obj=self.request.user,
        )
        form = form_class(instance=self.request.user)

        self.assertIn(
            f'value="{self.request.user.birth_date.isoformat()}"',
            str(form["birth_date"]),
        )

    def test_acceptance_is_read_only(self):
        model_admin = TermsAcceptanceAdmin(TermsAcceptance, self.site)
        self.assertFalse(model_admin.has_add_permission(self.request))
        self.assertFalse(model_admin.has_change_permission(self.request))
        self.assertFalse(model_admin.has_delete_permission(self.request))
        self.assertTrue(model_admin.has_view_permission(self.request))

    def test_terms_with_acceptances_cannot_be_deleted_from_admin(self):
        terms, _ = create_terms_versions()
        user = create_user(
            username="cliente",
            email="cliente@example.test",
            document="CLIENTE-001",
        )
        TermsAcceptance.objects.create(user=user, terms_version=terms)
        model_admin = TermsVersionAdmin(TermsVersion, self.site)

        self.assertFalse(model_admin.has_delete_permission(self.request, terms))
