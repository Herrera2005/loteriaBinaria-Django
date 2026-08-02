from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import ADMINISTRATOR, CLIENT
from apps.accounts.tests.factories import create_user
from apps.lottery.models import DrawEvent, LotteryProduct, Ticket


class EventAdministrationPermissionTests(TestCase):
    def setUp(self):
        self.administrator = create_user(
            username="admin_participante",
            email="admin-participante@example.test",
            document="ADMIN-PARTICIPANTE",
            roles=(CLIENT, ADMINISTRATOR),
            is_staff=True,
        )
        self.other_administrator = create_user(
            username="admin_libre",
            email="admin-libre@example.test",
            document="ADMIN-LIBRE",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        self.product = LotteryProduct.objects.create(
            code=LotteryProduct.Code.OCTAL,
            name="Octal",
            allowed_symbols="01234567",
            selection_count=4,
            is_active=True,
        )
        draw_at = timezone.now() + timedelta(days=2)
        self.event = DrawEvent.objects.create(
            product=self.product,
            name="Evento con participante administrador",
            sales_open_at=timezone.now() + timedelta(hours=1),
            draw_at=draw_at,
            price_minor=100,
            prize_minor=500,
            status=DrawEvent.Status.DRAFT,
        )
        Ticket.objects.create(
            user=self.administrator,
            event=self.event,
            normalized_key="0123",
            price_minor=100,
        )

    def _login_in_admin_mode(self, user):
        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

    def test_administrator_with_ticket_cannot_open_event_detail(self):
        self._login_in_admin_mode(self.administrator)

        response = self.client.get(
            reverse("lottery:event_detail", kwargs={"pk": self.event.pk})
        )

        self.assertEqual(response.status_code, 403)

    def test_administrator_with_ticket_cannot_update_or_delete_event(self):
        self._login_in_admin_mode(self.administrator)

        for route_name in ("lottery:event_update", "lottery:event_delete"):
            with self.subTest(route=route_name):
                response = self.client.get(
                    reverse(route_name, kwargs={"pk": self.event.pk})
                )
                self.assertEqual(response.status_code, 403)

    def test_administrator_with_ticket_does_not_see_event_in_admin_list(self):
        self._login_in_admin_mode(self.administrator)

        response = self.client.get(reverse("lottery:event_list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            self.event,
            list(response.context["events"]),
        )

    def test_other_administrator_can_administer_event(self):
        self._login_in_admin_mode(self.other_administrator)

        response = self.client.get(
            reverse("lottery:event_detail", kwargs={"pk": self.event.pk})
        )

        self.assertEqual(response.status_code, 200)
