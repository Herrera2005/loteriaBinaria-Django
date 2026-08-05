from __future__ import annotations

from datetime import time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import ADMINISTRATOR, CLIENT
from apps.accounts.tests.factories import create_user
from apps.core.date_utils import local_date_bounds
from apps.core.models import AuditEvent
from apps.lottery.models import DrawEvent, DrawEventStatusTransition, LotteryProduct


class CoreReadOnlyAndDateRegressionTests(TestCase):
    def _activate(self, user, mode):
        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = mode
        session.save()

    def test_client_dashboard_get_does_not_change_event_status(self):
        user = create_user(
            username="core_readonly_client",
            email="core-readonly-client@example.test",
            document="CORE-READONLY",
            roles=(CLIENT,),
        )
        rule = LotteryProduct.PRODUCT_RULES[LotteryProduct.Code.OCTAL]
        product = LotteryProduct.objects.create(
            kind=LotteryProduct.Kind.OFFICIAL,
            code=LotteryProduct.Code.OCTAL,
            name="Octal core",
            allowed_symbols=rule["allowed_symbols"],
            selection_count=rule["selection_count"],
        )
        now = timezone.now()
        event = DrawEvent.objects.create(
            product=product,
            name="Evento core sin escritura GET",
            sales_open_at=now - timedelta(minutes=5),
            draw_at=now + timedelta(hours=2),
            price_minor=100,
            prize_minor=5000,
            status=DrawEvent.Status.SCHEDULED,
        )
        before_updated = event.updated_at
        self._activate(user, CLIENT)

        response = self.client.get(reverse("core:client_dashboard"))

        self.assertEqual(response.status_code, 200)
        event.refresh_from_db()
        self.assertEqual(event.status, DrawEvent.Status.SCHEDULED)
        self.assertEqual(event.updated_at, before_updated)
        self.assertFalse(
            DrawEventStatusTransition.objects.filter(event=event).exists()
        )

    def test_local_date_bounds_are_aware_and_half_open(self):
        local_day = timezone.localdate()
        start, end = local_date_bounds(local_day)
        self.assertTrue(timezone.is_aware(start))
        self.assertTrue(timezone.is_aware(end))
        self.assertEqual(start.time(), time.min)
        self.assertEqual(end - start, timedelta(days=1))

    def test_audit_date_filters_use_local_half_open_bounds(self):
        admin = create_user(
            username="audit_date_admin",
            email="audit-date-admin@example.test",
            document="AUDIT-DATE-ADMIN",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        selected_day = timezone.localdate()
        start, end = local_date_bounds(selected_day)
        inside = AuditEvent.objects.create(
            actor=admin,
            active_mode=ADMINISTRATOR,
            action="INSIDE_LOCAL_DAY",
            resource_type="test",
            resource_id="1",
        )
        outside = AuditEvent.objects.create(
            actor=admin,
            active_mode=ADMINISTRATOR,
            action="OUTSIDE_LOCAL_DAY",
            resource_type="test",
            resource_id="2",
        )
        AuditEvent._base_manager.filter(pk=inside.pk).update(
            created_at=start + timedelta(minutes=1)
        )
        AuditEvent._base_manager.filter(pk=outside.pk).update(created_at=end)
        self._activate(admin, ADMINISTRATOR)

        response = self.client.get(
            reverse("core:audit_list"),
            {
                "date_from": selected_day.isoformat(),
                "date_to": selected_day.isoformat(),
            },
        )

        returned_ids = {event.pk for event in response.context["audit_events"]}
        self.assertIn(inside.pk, returned_ids)
        self.assertNotIn(outside.pk, returned_ids)
