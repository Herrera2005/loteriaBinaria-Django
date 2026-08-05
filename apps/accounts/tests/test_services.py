"""Pruebas del servicio de baja protegida de usuarios."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.accounts.models import TermsAcceptance, User
from apps.accounts.services import delete_or_deactivate_user

from .factories import create_terms_versions, create_user


class UserRemovalServiceTests(TestCase):
    def setUp(self):
        self.actor = create_user(
            username="actor_admin",
            email="actor-admin@example.test",
            document="ACTOR-ADMIN",
            is_staff=True,
        )

    def test_user_without_history_is_physically_deleted(self):
        target = create_user(
            username="sin_historia_servicio",
            email="sin-historia-servicio@example.test",
            document="SIN-HIST-SRV",
        )

        result = delete_or_deactivate_user(
            actor=self.actor,
            target_id=target.pk,
        )

        self.assertEqual(result.action, "deleted")
        self.assertEqual(result.username, "sin_historia_servicio")
        self.assertFalse(User.objects.filter(pk=target.pk).exists())

    def test_user_with_history_is_logically_deactivated(self):
        terms, _ = create_terms_versions()
        target = create_user(
            username="con_historia_servicio",
            email="con-historia-servicio@example.test",
            document="CON-HIST-SRV",
        )
        acceptance = TermsAcceptance.objects.create(
            user=target,
            terms_version=terms,
            ip_address="127.0.0.1",
        )

        result = delete_or_deactivate_user(
            actor=self.actor,
            target_id=target.pk,
        )

        self.assertEqual(result.action, "deactivated")
        target.refresh_from_db()
        self.assertEqual(target.status, User.Status.DISABLED)
        self.assertFalse(target.is_active)
        self.assertTrue(
            TermsAcceptance.objects.filter(pk=acceptance.pk).exists()
        )

    def test_actor_cannot_remove_own_account(self):
        with self.assertRaisesMessage(
            ValidationError,
            "No puedes eliminar ni desactivar tu propia cuenta",
        ):
            delete_or_deactivate_user(
                actor=self.actor,
                target_id=self.actor.pk,
            )

        self.actor.refresh_from_db()
        self.assertTrue(self.actor.is_active)

    def test_superuser_is_protected(self):
        target = create_user(
            username="superuser_protegido",
            email="superuser-protegido@example.test",
            document="SUPERUSER-PROTEGIDO",
            is_staff=True,
            is_superuser=True,
        )

        with self.assertRaisesMessage(
            ValidationError,
            "Los superusuarios no se eliminan ni desactivan",
        ):
            delete_or_deactivate_user(
                actor=self.actor,
                target_id=target.pk,
            )

        target.refresh_from_db()
        self.assertTrue(target.is_active)
