from datetime import timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.accounts.roles import ADMINISTRATOR, CLIENT
from apps.accounts.tests.factories import create_user
from apps.finance.models import Movement, Wallet
from apps.lottery.models import DrawEvent, DrawEventSeries, DrawResult, LotteryProduct, Ticket
from apps.lottery.services import (
    process_due_automatic_results,
    sync_lottery_event_states,
    transition_draw_event,
)

class AutomaticResultTests(TestCase):
    def setUp(self):
        self.admin = create_user(
            username="automatic_admin",
            email="automatic-admin@example.test",
            document="AUTO-ADMIN",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        self.client_user = create_user(
            username="automatic_client",
            email="automatic-client@example.test",
            document="AUTO-CLIENT",
            roles=(CLIENT,),
        )
        rule = LotteryProduct.PRODUCT_RULES[LotteryProduct.Code.OCTAL]
        self.product = LotteryProduct.objects.create(
            kind=LotteryProduct.Kind.OFFICIAL,
            code=LotteryProduct.Code.OCTAL,
            name="Octal automático",
            allowed_symbols=rule["allowed_symbols"],
            selection_count=rule["selection_count"],
        )
        now = timezone.now()
        self.series = DrawEventSeries.objects.create(
            name_prefix="Octal automático",
            product=self.product,
            first_draw_at=now - timedelta(minutes=1),
            next_draw_at=now + timedelta(hours=1),
            recurrence_minutes=60,
            sales_lead_minutes=30,
            price_minor=100,
            prize_minor=5000,
            future_events_target=1,
            result_mode=DrawEventSeries.ResultMode.AUTOMATIC,
            is_active=False,
            created_by=self.admin,
        )
        self.event = DrawEvent.objects.create(
            series=self.series,
            series_sequence=1,
            product=self.product,
            name="Octal automático #1",
            sales_open_at=now - timedelta(hours=1),
            draw_at=now - timedelta(minutes=1),
            price_minor=100,
            prize_minor=5000,
            status=DrawEvent.Status.SALES_CLOSED,
        )

    @patch("apps.lottery.services.generate_automatic_winning_key", return_value="0123")
    def test_due_automatic_event_is_published_and_finished(self, _generator):
        Ticket.objects.create(
            user=self.client_user,
            event=self.event,
            normalized_key="0123",
            price_minor=100,
        )
        outcome = process_due_automatic_results()

        self.event.refresh_from_db()
        result = DrawResult.objects.get(event=self.event)
        wallet = Wallet.objects.get(user=self.client_user, currency=Wallet.Currency.VIRTUAL)

        self.assertEqual(outcome.processed_event_ids, (self.event.pk,))
        self.assertEqual(result.publication_source, DrawResult.PublicationSource.SYSTEM)
        self.assertIsNone(result.published_by)
        self.assertEqual(result.winning_key, "0123")
        self.assertEqual(self.event.status, DrawEvent.Status.FINISHED)
        self.assertEqual(wallet.available_minor, 5000)

    @patch("apps.lottery.services.generate_automatic_winning_key", return_value="0123")
    def test_reprocessing_does_not_duplicate_result_or_prize(self, _generator):
        Ticket.objects.create(
            user=self.client_user,
            event=self.event,
            normalized_key="0123",
            price_minor=100,
        )
        process_due_automatic_results()
        movement_count = Movement.objects.filter(type=Movement.Type.PRIZE).count()
        second = process_due_automatic_results()

        self.assertEqual(second.processed_event_ids, ())
        self.assertEqual(DrawResult.objects.filter(event=self.event).count(), 1)
        self.assertEqual(Movement.objects.filter(type=Movement.Type.PRIZE).count(), movement_count)

    def test_manual_series_is_not_processed(self):
        self.series.result_mode = DrawEventSeries.ResultMode.MANUAL
        self.series.save(update_fields=("result_mode", "updated_at"))
        outcome = process_due_automatic_results()
        self.assertEqual(outcome.processed_event_ids, ())
        self.assertFalse(DrawResult.objects.filter(event=self.event).exists())

    def test_future_event_is_not_processed(self):
        now = timezone.now()

        future_event = DrawEvent.objects.create(
            series=self.series,
            series_sequence=2,
            product=self.product,
            name="Octal automático futuro #2",
            sales_open_at=now - timedelta(minutes=5),
            draw_at=now + timedelta(minutes=15),
            price_minor=100,
            prize_minor=5000,
            status=DrawEvent.Status.SALES_CLOSED,
        )

        outcome = process_due_automatic_results()

        self.assertNotIn(
            future_event.pk,
            outcome.processed_event_ids,
        )
        self.assertFalse(
            DrawResult.objects.filter(
                event=future_event,
            ).exists()
        )

    def test_cancelled_event_is_not_processed(self):
        transition_draw_event(
            event_id=self.event.pk,
            to_status=DrawEvent.Status.CANCELLED,
            actor=self.admin,
            reason="Cancelación preparada para la prueba automática.",
            public_message="El sorteo fue cancelado para una prueba.",
        )

        outcome = process_due_automatic_results()

        self.event.refresh_from_db()

        self.assertEqual(
            self.event.status,
            DrawEvent.Status.CANCELLED,
        )
        self.assertNotIn(
            self.event.pk,
            outcome.processed_event_ids,
        )
        self.assertFalse(
            DrawResult.objects.filter(
                event=self.event,
            ).exists()
        )

    def test_sync_closes_scheduled_event_when_close_time_was_missed(self):
        now = timezone.now()

        scheduled_event = DrawEvent.objects.create(
            series=self.series,
            series_sequence=2,
            product=self.product,
            name="Octal programado vencido #2",
            sales_open_at=now - timedelta(hours=1),
            draw_at=now - timedelta(minutes=1),
            price_minor=100,
            prize_minor=5000,
            status=DrawEvent.Status.SCHEDULED,
        )

        changed = sync_lottery_event_states(
            now=now,
        )

        scheduled_event.refresh_from_db()

        self.assertEqual(changed, 1)
        self.assertEqual(
            scheduled_event.status,
            DrawEvent.Status.SALES_CLOSED,
        )

    @patch("apps.lottery.services.generate_automatic_winning_key", return_value="0123")
    def test_management_command_processes_automatic_result(self, _generator):
        call_command("process_lottery_schedules")
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, DrawEvent.Status.FINISHED)
        self.assertTrue(DrawResult.objects.filter(event=self.event).exists())
