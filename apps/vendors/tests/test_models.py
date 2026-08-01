"""Pruebas de modelos y formulario del módulo vendors."""

from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.roles import CLIENT, VENDOR
from apps.accounts.tests.factories import create_user
from apps.vendors import forms as vendor_forms
from apps.vendors.forms import VendorProfileForm
from apps.vendors.models import (
    ConversionAssignment,
    ConversionRequest,
    VendorProfile,
)


def create_vendor_user(
    *,
    username: str = "vendedor_prueba",
    email: str = "vendedor@example.test",
    document: str = "VEND-001",
    status: str = User.Status.ACTIVE,
):
    return create_user(
        username=username,
        email=email,
        document=document,
        status=status,
        roles=(VENDOR,),
    )


def create_client_user(
    *,
    username: str = "cliente_vendor_flow",
    email: str = "cliente-flow@example.test",
    document: str = "CLI-FLOW-001",
):
    return create_user(
        username=username,
        email=email,
        document=document,
        roles=(CLIENT,),
    )


def create_vendor_profile(
    *,
    user=None,
    status: str = VendorProfile.Status.ACTIVE,
):
    user = user or create_vendor_user()
    profile = VendorProfile(user=user, status=status)
    profile.full_clean()
    profile.save()
    return profile


def create_conversion_request(*, client=None, amount_minor: int = 1000):
    client = client or create_client_user()
    return ConversionRequest.objects.create(
        client=client,
        amount_minor=amount_minor,
        expires_at=timezone.now() + timedelta(minutes=5),
    )


class VendorProfileModelTests(TestCase):
    def test_user_can_have_only_one_vendor_profile(self):
        user = create_vendor_user()
        create_vendor_profile(user=user)

        with self.assertRaises(IntegrityError), transaction.atomic():
            VendorProfile.objects.create(user=user)

    def test_profile_uses_one_to_one_and_protects_user(self):
        field = VendorProfile._meta.get_field("user")

        self.assertTrue(field.one_to_one)
        self.assertIs(field.remote_field.on_delete, models.PROTECT)

        user = create_vendor_user()
        create_vendor_profile(user=user)
        with self.assertRaises(models.ProtectedError):
            user.delete()

    def test_profile_requires_vendor_role(self):
        user = create_user(
            username="sin_rol_vendedor",
            email="sin-rol@example.test",
            document="SIN-VEND-001",
        )
        profile = VendorProfile(
            user=user,
            status=VendorProfile.Status.PENDING,
        )

        with self.assertRaises(ValidationError) as context:
            profile.full_clean()

        self.assertIn("user", context.exception.message_dict)

    def test_active_profile_requires_active_account(self):
        user = create_vendor_user(
            username="vendedor_suspendido_modelo",
            email="vendedor-suspendido-modelo@example.test",
            document="VEND-SUSP-MOD",
            status=User.Status.SUSPENDED,
        )
        profile = VendorProfile(
            user=user,
            status=VendorProfile.Status.ACTIVE,
        )

        with self.assertRaises(ValidationError) as context:
            profile.full_clean()

        self.assertIn("status", context.exception.message_dict)

    def test_active_profile_sets_activation_date(self):
        profile = create_vendor_profile()

        self.assertIsNotNone(profile.activated_at)


class ConversionRequestModelTests(TestCase):
    def test_amount_uses_big_integer_minor_units(self):
        field = ConversionRequest._meta.get_field("amount_minor")

        self.assertIsInstance(field, models.BigIntegerField)
        self.assertNotIsInstance(field, models.FloatField)
        self.assertNotIsInstance(field, models.DecimalField)

    def test_amount_minor_must_be_positive(self):
        request = ConversionRequest(
            client=create_client_user(),
            amount_minor=0,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        with self.assertRaises(ValidationError) as context:
            request.full_clean()

        self.assertIn("amount_minor", context.exception.message_dict)

    def test_expiration_must_be_after_creation(self):
        client = create_client_user()

        with self.assertRaises(IntegrityError), transaction.atomic():
            ConversionRequest.objects.create(
                client=client,
                amount_minor=1000,
                expires_at=timezone.now() - timedelta(minutes=1),
            )

    def test_operation_id_is_unique(self):
        first = create_conversion_request()
        second_client = create_client_user(
            username="cliente_segundo",
            email="cliente-segundo@example.test",
            document="CLI-FLOW-002",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            ConversionRequest.objects.create(
                client=second_client,
                operation_id=first.operation_id,
                amount_minor=2000,
                expires_at=timezone.now() + timedelta(minutes=5),
            )

    def test_request_is_historical_and_cannot_be_deleted(self):
        request = create_conversion_request()

        with self.assertRaises(ValidationError):
            request.delete()

        with self.assertRaises(ValidationError):
            ConversionRequest.objects.filter(pk=request.pk).delete()

    def test_request_uses_protected_client_relation(self):
        field = ConversionRequest._meta.get_field("client")
        self.assertIs(field.remote_field.on_delete, models.PROTECT)

        client = create_client_user()
        create_conversion_request(client=client)
        with self.assertRaises(models.ProtectedError):
            client.delete()


class ConversionAssignmentModelTests(TestCase):
    def test_assignment_uses_protected_relations(self):
        request_field = ConversionAssignment._meta.get_field("request")
        vendor_field = ConversionAssignment._meta.get_field("vendor")

        self.assertIs(request_field.remote_field.on_delete, models.PROTECT)
        self.assertIs(vendor_field.remote_field.on_delete, models.PROTECT)

        profile = create_vendor_profile()
        assignment = ConversionAssignment.objects.create(
            request=create_conversion_request(),
            vendor=profile,
        )

        with self.assertRaises(models.ProtectedError):
            profile.delete()

        self.assertTrue(
            ConversionAssignment.objects.filter(pk=assignment.pk).exists()
        )

    def test_assignment_is_historical_and_cannot_be_deleted(self):
        assignment = ConversionAssignment.objects.create(
            request=create_conversion_request(),
            vendor=create_vendor_profile(),
        )

        with self.assertRaises(ValidationError):
            assignment.delete()

        with self.assertRaises(ValidationError):
            ConversionAssignment.objects.filter(pk=assignment.pk).delete()

    def test_assignment_has_no_conditional_unique_constraint(self):
        unique_constraints = [
            constraint
            for constraint in ConversionAssignment._meta.constraints
            if isinstance(constraint, models.UniqueConstraint)
        ]

        self.assertTrue(unique_constraints)
        self.assertTrue(
            all(constraint.condition is None for constraint in unique_constraints)
        )


class VendorProfileFormTests(TestCase):
    def test_valid_vendor_profile_is_created(self):
        user = create_vendor_user()
        form = VendorProfileForm(
            data={
                "user": user.pk,
                "status": VendorProfile.Status.ACTIVE,
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        profile = form.save()

        self.assertEqual(profile.user, user)
        self.assertEqual(profile.status, VendorProfile.Status.ACTIVE)
        self.assertIsNotNone(profile.activated_at)

    def test_user_without_vendor_role_is_not_eligible(self):
        user = create_user(
            username="cliente_sin_vendor",
            email="cliente-sin-vendor@example.test",
            document="CLI-SIN-VEND",
        )
        form = VendorProfileForm(
            data={
                "user": user.pk,
                "status": VendorProfile.Status.PENDING,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("user", form.errors)

    def test_inactive_user_is_not_eligible(self):
        user = create_vendor_user(
            username="vendedor_suspendido",
            email="vendedor-suspendido@example.test",
            document="VEND-SUSP",
            status=User.Status.SUSPENDED,
        )
        form = VendorProfileForm(
            data={
                "user": user.pk,
                "status": VendorProfile.Status.PENDING,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("user", form.errors)

    def test_duplicate_profile_is_rejected(self):
        profile = create_vendor_profile()
        form = VendorProfileForm(
            data={
                "user": profile.user_id,
                "status": VendorProfile.Status.PENDING,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("user", form.errors)

    def test_update_keeps_original_user_and_changes_status(self):
        profile = create_vendor_profile()
        form = VendorProfileForm(
            instance=profile,
            data={
                "user": profile.user_id,
                "status": VendorProfile.Status.SUSPENDED,
            },
        )

        self.assertTrue(form.fields["user"].disabled)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        updated = form.save()

        self.assertEqual(updated.user_id, profile.user_id)
        self.assertEqual(updated.status, VendorProfile.Status.SUSPENDED)

    def test_existing_profile_can_be_disabled_after_account_suspension(self):
        profile = create_vendor_profile()
        user = profile.user
        user.status = User.Status.SUSPENDED
        user.is_active = False
        user.save(update_fields=("status", "is_active", "updated_at"))

        form = VendorProfileForm(
            instance=profile,
            data={
                "user": user.pk,
                "status": VendorProfile.Status.DISABLED,
            },
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        updated = form.save()
        self.assertEqual(updated.status, VendorProfile.Status.DISABLED)

    def test_widgets_use_bootstrap_classes(self):
        form = VendorProfileForm()

        self.assertIn("form-select", form.fields["user"].widget.attrs["class"])
        self.assertIn(
            "form-select",
            form.fields["status"].widget.attrs["class"],
        )

    def test_flow_models_do_not_have_generic_model_forms(self):
        self.assertFalse(hasattr(vendor_forms, "ConversionRequestForm"))
        self.assertFalse(hasattr(vendor_forms, "ConversionAssignmentForm"))
