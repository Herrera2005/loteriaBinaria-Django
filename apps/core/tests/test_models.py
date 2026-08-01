"""Pruebas P-28A de AuditEvent y administración read-only."""

from __future__ import annotations

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
from django.test import RequestFactory, TestCase

from apps.accounts.roles import ADMINISTRATOR
from apps.accounts.tests.factories import create_user
from apps.core.admin import AuditEventAdmin
from apps.core.models import AuditEvent


def create_actor():
    return create_user(
        username="audit_actor",
        email="audit.actor@example.test",
        document="AUDIT-ACTOR-001",
        is_staff=True,
        is_superuser=True,
    )


def create_audit_event(**overrides):
    values = {
        "actor": create_actor(),
        "active_mode": ADMINISTRATOR,
        "action": "TEST_ACTION",
        "resource_type": "finance.Wallet",
        "resource_id": "1",
        "reason": "Prueba académica controlada.",
        "metadata": "resultado=permitido",
        "ip_address": "127.0.0.1",
    }
    values.update(overrides)
    return AuditEvent.objects.create(**values)


class AuditEventModelTests(TestCase):
    def test_actor_relation_uses_protect(self):
        actor = create_actor()
        field = AuditEvent._meta.get_field("actor")

        self.assertIs(field.remote_field.on_delete, models.PROTECT)
        AuditEvent.objects.create(
            actor=actor,
            active_mode=ADMINISTRATOR,
            action="PROTECTED_ACTOR",
            resource_type="accounts.User",
            resource_id=str(actor.pk),
        )

        with self.assertRaises(models.ProtectedError):
            actor.delete()

    def test_audit_event_accepts_minimal_non_sensitive_data(self):
        event = create_audit_event()

        self.assertIsNotNone(event.pk)
        self.assertEqual(event.active_mode, ADMINISTRATOR)
        self.assertEqual(event.action, "TEST_ACTION")

    def test_sensitive_metadata_is_rejected(self):
        event = AuditEvent(
            actor=create_actor(),
            active_mode=ADMINISTRATOR,
            action="SECRET_ATTEMPT",
            resource_type="accounts.User",
            resource_id="1",
            metadata="token=abc123",
        )

        with self.assertRaises(ValidationError) as context:
            event.full_clean()

        self.assertIn("metadata", context.exception.message_dict)

    def test_existing_audit_event_cannot_be_saved_again(self):
        event = create_audit_event()
        event.reason = "Intento de reescritura"

        with self.assertRaises(ValidationError):
            event.save()

    def test_audit_event_cannot_be_deleted_individually_or_in_bulk(self):
        event = create_audit_event()

        with self.assertRaises(ValidationError):
            event.delete()

        with self.assertRaises(ValidationError):
            AuditEvent.objects.filter(pk=event.pk).delete()

    def test_audit_event_cannot_be_updated_in_bulk(self):
        event = create_audit_event()

        with self.assertRaises(ValidationError):
            AuditEvent.objects.filter(pk=event.pk).update(
                reason="Intento masivo"
            )

        with self.assertRaises(ValidationError):
            AuditEvent.objects.bulk_update(
                [event],
                ["reason"],
            )

    def test_resource_and_actor_indexes_are_declared(self):
        index_names = {index.name for index in AuditEvent._meta.indexes}

        self.assertIn("core_audit_actor_date_idx", index_names)
        self.assertIn("core_audit_action_date_idx", index_names)
        self.assertIn("core_audit_resource_idx", index_names)


class AuditAdminReadOnlyTests(TestCase):
    def test_audit_admin_is_read_only(self):
        request = RequestFactory().get("/admin/")
        request.user = create_actor()
        model_admin = AuditEventAdmin(AuditEvent, admin.site)

        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request))
        self.assertTrue(model_admin.has_view_permission(request))
