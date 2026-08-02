from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.accounts.roles import ADMINISTRATOR
from apps.accounts.tests.factories import create_user
from apps.lottery.models import DrawEvent, DrawEventSeries, LotteryProduct
from apps.lottery.services import generate_series_events, process_active_event_series


class DrawEventSeriesTests(TestCase):
    def setUp(self):
        self.admin = create_user(
            username="series_admin",
            email="series-admin@example.test",
            document="SERIES-ADMIN",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        rule = LotteryProduct.PRODUCT_RULES[LotteryProduct.Code.OCTAL]
        self.product = LotteryProduct.objects.create(
            kind=LotteryProduct.Kind.OFFICIAL,
            code=LotteryProduct.Code.OCTAL,
            name="Octal",
            allowed_symbols=rule["allowed_symbols"],
            selection_count=rule["selection_count"],
        )
        self.first_draw = timezone.now() + timedelta(hours=8)
        self.series = DrawEventSeries.objects.create(
            name_prefix="Octal Diario",
            product=self.product,
            first_draw_at=self.first_draw,
            recurrence_minutes=1440,
            sales_lead_minutes=480,
            price_minor=100,
            prize_minor=5000,
            future_events_target=2,
            created_by=self.admin,
        )

    def test_generates_numbered_future_events(self):
        result = generate_series_events(series_id=self.series.pk, actor=self.admin)
        self.assertEqual(len(result.created_event_ids), 2)
        events = list(self.series.events.order_by("series_sequence"))
        self.assertEqual([event.name for event in events], ["Octal Diario #1", "Octal Diario #2"])
        self.assertTrue(all(event.status in {DrawEvent.Status.SCHEDULED, DrawEvent.Status.SALES_OPEN} for event in events))

    def test_generation_is_idempotent(self):
        generate_series_events(series_id=self.series.pk, actor=self.admin)
        second = generate_series_events(series_id=self.series.pk, actor=self.admin)
        self.assertEqual(second.created_event_ids, ())
        self.assertEqual(self.series.events.count(), 2)

    def test_paused_series_creates_nothing(self):
        self.series.is_active = False
        self.series.save(update_fields=("is_active", "updated_at"))
        result = generate_series_events(series_id=self.series.pk, actor=self.admin)
        self.assertEqual(result.created_event_ids, ())

    def test_processor_and_command_are_repeatable(self):
        process_active_event_series(actor=self.admin)
        call_command("process_lottery_schedules")
        self.assertEqual(self.series.events.count(), 2)


class DrawEventSeriesLimitTests(DrawEventSeriesTests):
    def test_limited_series_stops_after_remaining_occurrences(self):
        self.series.future_events_target = 5
        self.series.remaining_occurrences = 3
        self.series.save(
            update_fields=(
                "future_events_target",
                "remaining_occurrences",
                "updated_at",
            )
        )

        result = generate_series_events(series_id=self.series.pk, actor=self.admin)

        self.series.refresh_from_db()
        self.assertEqual(len(result.created_event_ids), 3)
        self.assertEqual(self.series.events.count(), 3)
        self.assertEqual(self.series.remaining_occurrences, 0)
        self.assertFalse(self.series.is_active)

    def test_unlimited_series_only_maintains_future_target(self):
        self.series.remaining_occurrences = None
        self.series.save(update_fields=("remaining_occurrences", "updated_at"))

        first = generate_series_events(series_id=self.series.pk, actor=self.admin)
        second = generate_series_events(series_id=self.series.pk, actor=self.admin)

        self.assertEqual(len(first.created_event_ids), 2)
        self.assertEqual(second.created_event_ids, ())
        self.series.refresh_from_db()
        self.assertIsNone(self.series.remaining_occurrences)
        self.assertTrue(self.series.is_active)

    def test_editing_schedule_changes_only_not_generated_events(self):
        generate_series_events(series_id=self.series.pk, actor=self.admin)
        existing_dates = list(
            self.series.events.order_by("series_sequence")
            .values_list("draw_at", flat=True)
        )
        self.series.refresh_from_db()
        self.series.recurrence_minutes = 720
        self.series.next_draw_at = existing_dates[-1] + timedelta(hours=12)
        self.series.future_events_target = 3
        self.series.save(
            update_fields=(
                "recurrence_minutes",
                "next_draw_at",
                "future_events_target",
                "updated_at",
            )
        )

        generate_series_events(series_id=self.series.pk, actor=self.admin)

        self.assertEqual(
            list(
                self.series.events.order_by("series_sequence")[:2]
                .values_list("draw_at", flat=True)
            ),
            existing_dates,
        )
        third = self.series.events.get(series_sequence=3)
        self.assertEqual(third.draw_at, existing_dates[-1] + timedelta(hours=12))

    def test_archived_series_never_generates_again(self):
        from apps.lottery.services import archive_event_series

        generate_series_events(series_id=self.series.pk, actor=self.admin)
        archived = archive_event_series(series_id=self.series.pk, actor=self.admin)
        second = generate_series_events(series_id=self.series.pk, actor=self.admin)

        self.series.refresh_from_db()
        self.assertTrue(archived.deleted)
        self.assertTrue(self.series.is_archived)
        self.assertFalse(self.series.is_active)
        self.assertEqual(second.created_event_ids, ())
        self.assertEqual(self.series.events.count(), 2)
