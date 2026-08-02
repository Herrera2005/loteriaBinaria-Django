from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import ADMINISTRATOR, CLIENT
from apps.accounts.tests.factories import create_user
from apps.finance.models import Movement, Wallet
from apps.lottery.forms import DrawResultPublishForm
from apps.lottery.models import (
    DrawEvent,
    DrawEventStatusTransition,
    DrawResult,
    LotteryProduct,
    Ticket,
)
from apps.lottery.services import publish_draw_result, settle_draw_result


def create_product():
    return LotteryProduct.objects.create(
        code=LotteryProduct.Code.OCTAL,
        name="Octal resultado",
        allowed_symbols="01234567",
        selection_count=4,
        is_active=True,
    )


def create_closed_event(*, product=None, draw_delta=-5):
    product = product or create_product()
    now = timezone.now()
    return DrawEvent.objects.create(
        product=product,
        name="Evento para resultado",
        sales_open_at=now - timedelta(hours=2),
        draw_at=now + timedelta(minutes=draw_delta),
        price_minor=250,
        prize_minor=10000,
        status=DrawEvent.Status.SALES_CLOSED,
    )


def create_admin(username="result_admin"):
    return create_user(
        username=username,
        email=f"{username}@example.test",
        document=f"DOC-{username}",
        roles=(ADMINISTRATOR,),
        is_staff=True,
    )


def create_client(username):
    return create_user(
        username=username,
        email=f"{username}@example.test",
        document=f"DOC-{username}",
        roles=(CLIENT,),
    )


class ResultPublicationServiceTests(TestCase):
    def setUp(self):
        self.admin = create_admin()
        self.event = create_closed_event()
        self.winner = create_client("winner_client")
        self.near = create_client("near_client")
        self.loser = create_client("loser_client")
        self.winner_ticket = Ticket.objects.create(
            user=self.winner,
            event=self.event,
            normalized_key="3210",
            price_minor=self.event.price_minor,
        )
        self.near_ticket = Ticket.objects.create(
            user=self.near,
            event=self.event,
            normalized_key="0124",
            price_minor=self.event.price_minor,
        )
        self.loser_ticket = Ticket.objects.create(
            user=self.loser,
            event=self.event,
            normalized_key="0456",
            price_minor=self.event.price_minor,
        )

    def test_publish_evaluates_credits_and_finishes(self):
        winner_wallet = Wallet.objects.get(
            user=self.winner,
            currency=Wallet.Currency.VIRTUAL,
        )
        near_wallet = Wallet.objects.get(
            user=self.near,
            currency=Wallet.Currency.VIRTUAL,
        )

        outcome = publish_draw_result(
            event_id=self.event.pk,
            winning_key="3012",
            actor=self.admin,
            reason="Acta académica verificada.",
        )

        self.event.refresh_from_db()
        self.winner_ticket.refresh_from_db()
        self.near_ticket.refresh_from_db()
        self.loser_ticket.refresh_from_db()
        winner_wallet.refresh_from_db()
        near_wallet.refresh_from_db()

        self.assertEqual(outcome.result.winning_key, "0123")
        self.assertEqual(self.event.status, DrawEvent.Status.FINISHED)
        self.assertEqual(outcome.winner_count, 1)
        self.assertEqual(outcome.refund_count, 1)
        self.assertEqual(outcome.not_winner_count, 1)
        self.assertEqual(outcome.credited_count, 2)

        self.assertEqual(
            self.winner_ticket.evaluation_status,
            Ticket.EvaluationStatus.WINNER,
        )
        self.assertEqual(self.winner_ticket.award_minor, 10000)
        self.assertIsNotNone(self.winner_ticket.credited_at)
        self.assertIsNotNone(self.winner_ticket.award_operation_id)
        self.assertEqual(winner_wallet.available_minor, 10000)

        self.assertEqual(
            self.near_ticket.evaluation_status,
            Ticket.EvaluationStatus.REFUND,
        )
        self.assertEqual(self.near_ticket.award_minor, 250)
        self.assertEqual(near_wallet.available_minor, 250)

        self.assertEqual(
            self.loser_ticket.evaluation_status,
            Ticket.EvaluationStatus.NOT_WINNER,
        )
        self.assertEqual(self.loser_ticket.award_minor, 0)
        self.assertIsNone(self.loser_ticket.credited_at)
        self.assertEqual(
            Movement.objects.filter(type=Movement.Type.PRIZE).count(),
            2,
        )
        self.assertTrue(
            DrawEventStatusTransition.objects.filter(
                event=self.event,
                to_status=DrawEvent.Status.RESULT_SET,
            ).exists()
        )
        self.assertTrue(
            DrawEventStatusTransition.objects.filter(
                event=self.event,
                to_status=DrawEvent.Status.FINISHED,
            ).exists()
        )

    def test_second_publication_is_rejected_and_keeps_first(self):
        first = publish_draw_result(
            event_id=self.event.pk,
            winning_key="0123",
            actor=self.admin,
            reason="Primer resultado.",
        )

        with self.assertRaises(ValidationError):
            publish_draw_result(
                event_id=self.event.pk,
                winning_key="4567",
                actor=self.admin,
                reason="Segundo resultado.",
            )

        self.assertEqual(DrawResult.objects.filter(event=self.event).count(), 1)
        self.assertEqual(
            DrawResult.objects.get(event=self.event).pk,
            first.result.pk,
        )

    def test_reprocessing_does_not_duplicate_prizes(self):
        outcome = publish_draw_result(
            event_id=self.event.pk,
            winning_key="0123",
            actor=self.admin,
            reason="Resultado verificado.",
        )
        balances_before = dict(
            Wallet.objects.filter(currency=Wallet.Currency.VIRTUAL)
            .values_list("user_id", "available_minor")
        )
        movements_before = Movement.objects.filter(
            type=Movement.Type.PRIZE
        ).count()

        repeated = settle_draw_result(result_id=outcome.result.pk)

        balances_after = dict(
            Wallet.objects.filter(currency=Wallet.Currency.VIRTUAL)
            .values_list("user_id", "available_minor")
        )
        self.assertEqual(repeated.credited_count, 0)
        self.assertEqual(balances_after, balances_before)
        self.assertEqual(
            Movement.objects.filter(type=Movement.Type.PRIZE).count(),
            movements_before,
        )

    def test_result_cannot_be_published_before_draw_time(self):
        event = create_closed_event(
            product=self.event.product,
            draw_delta=5,
        )
        with self.assertRaises(ValidationError):
            publish_draw_result(
                event_id=event.pk,
                winning_key="0123",
                actor=self.admin,
                reason="Demasiado temprano.",
            )
        self.assertFalse(DrawResult.objects.filter(event=event).exists())

    def test_administrator_participant_cannot_publish(self):
        participant = create_user(
            username="participant_admin",
            email="participant@example.test",
            document="DOC-PARTICIPANT",
            roles=(CLIENT, ADMINISTRATOR),
            is_staff=True,
        )
        Ticket.objects.create(
            user=participant,
            event=self.event,
            normalized_key="1234",
            price_minor=self.event.price_minor,
        )
        with self.assertRaises(ValidationError):
            publish_draw_result(
                event_id=self.event.pk,
                winning_key="0123",
                actor=participant,
                reason="Conflicto de interés.",
            )


class ResultPublicationFormTests(TestCase):
    def test_form_uses_dynamic_positions_and_rejects_repetition(self):
        event = create_closed_event()
        form = DrawResultPublishForm(
            data={
                "position_1": "0",
                "position_2": "0",
                "position_3": "1",
                "position_4": "2",
                "reason": "Verificación.",
            },
            event=event,
        )
        self.assertEqual(len(form.position_fields), 4)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)


class ResultPublicationViewTests(TestCase):
    def setUp(self):
        self.admin = create_admin("view_result_admin")
        self.event = create_closed_event()
        self.client.force_login(self.admin)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

    def test_admin_can_publish_from_visual_flow(self):
        response = self.client.post(
            reverse("lottery:result_publish", args=(self.event.pk,)),
            {
                "position_1": "3",
                "position_2": "2",
                "position_3": "1",
                "position_4": "0",
                "reason": "Acta revisada por el Administrador.",
            },
        )
        self.assertRedirects(
            response,
            reverse("lottery:event_detail", args=(self.event.pk,)),
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, DrawEvent.Status.FINISHED)
        self.assertEqual(self.event.result.winning_key, "0123")

    def test_public_result_has_aggregates_without_personal_data(self):
        private_client = create_client("private_winner")
        Ticket.objects.create(
            user=private_client,
            event=self.event,
            normalized_key="0123",
            price_minor=self.event.price_minor,
        )
        outcome = publish_draw_result(
            event_id=self.event.pk,
            winning_key="0123",
            actor=self.admin,
            reason="Publicación pública.",
        )
        self.client.logout()

        response = self.client.get(
            reverse(
                "lottery:public_result_detail",
                args=(outcome.result.pk,),
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0123")
        self.assertContains(response, "Ganadores")
        self.assertNotContains(response, private_client.username)
        self.assertNotContains(response, private_client.email)
        self.assertNotContains(response, private_client.document)
