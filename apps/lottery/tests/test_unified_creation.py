from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import ADMINISTRATOR
from apps.accounts.tests.factories import create_user
from apps.lottery.models import DrawEvent, DrawEventSeries, LotteryProduct


class UnifiedDrawCreationTests(TestCase):
    def setUp(self):
        self.admin = create_user(
            username="unified_admin",
            email="unified-admin@example.test",
            document="UNIFIED-ADMIN",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        self.client.force_login(self.admin)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()
        rule = LotteryProduct.PRODUCT_RULES[LotteryProduct.Code.OCTAL]
        self.product = LotteryProduct.objects.create(
            kind=LotteryProduct.Kind.OFFICIAL,
            code=LotteryProduct.Code.OCTAL,
            name="Octal",
            allowed_symbols=rule["allowed_symbols"],
            selection_count=rule["selection_count"],
        )

    def test_create_page_contains_both_modes(self):
        response = self.client.get(reverse("lottery:event_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Evento individual")
        self.assertContains(response, "Serie automática")
        self.assertIn("event_form", response.context)
        self.assertIn("series_form", response.context)

    def test_unified_page_creates_limited_series(self):
        first_draw = timezone.localtime() + timedelta(days=2)
        response = self.client.post(
            reverse("lottery:event_create"),
            {
                "creation_mode": "series",
                "series-name_prefix": "Octal Semanal",
                "series-product": self.product.pk,
                "series-first_draw_at": first_draw.strftime("%Y-%m-%dT%H:%M"),
                "series-next_draw_at": first_draw.strftime("%Y-%m-%dT%H:%M"),
                "series-recurrence_minutes": 10080,
                "series-sales_lead_minutes": 1440,
                "series-price_minor": "1.00",
                "series-prize_minor": "50.00",
                "series-future_events_target": 2,
                "series-occurrence_mode": "LIMITED",
                "series-remaining_occurrences": 4,
                "series-is_active": "on",
            },
        )

        series = DrawEventSeries.objects.get(name_prefix="Octal Semanal")
        self.assertRedirects(
            response,
            reverse("lottery:series_detail", args=(series.pk,)),
        )
        self.assertEqual(series.events.count(), 2)
        series.refresh_from_db()
        self.assertEqual(series.remaining_occurrences, 2)

    def test_legacy_event_post_still_creates_single_event(self):
        draw_at = timezone.localtime() + timedelta(days=3)
        response = self.client.post(
            reverse("lottery:event_create"),
            {
                "product": self.product.pk,
                "name": "Evento legado",
                "sales_open_at": (
                    timezone.localtime() + timedelta(hours=1)
                ).strftime("%Y-%m-%dT%H:%M"),
                "draw_at": draw_at.strftime("%Y-%m-%dT%H:%M"),
                "price_minor": "1.00",
                "prize_minor": "50.00",
            },
        )
        event = DrawEvent.objects.get(name="Evento legado")
        self.assertRedirects(
            response,
            reverse("lottery:event_detail", args=(event.pk,)),
        )
