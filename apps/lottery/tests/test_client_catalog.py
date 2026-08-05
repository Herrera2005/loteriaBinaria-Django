from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import CLIENT, VENDOR
from apps.accounts.tests.factories import create_user
from apps.lottery.models import DrawEvent, LotteryProduct, Ticket


def make_product():
    return LotteryProduct.objects.create(
        code=LotteryProduct.Code.OCTAL,
        name="Octal",
        allowed_symbols="01234567",
        selection_count=4,
        is_active=True,
    )


def make_event(product, name, status):
    now = timezone.now()
    return DrawEvent.objects.create(
        product=product,
        name=name,
        sales_open_at=now - timedelta(hours=1),
        draw_at=now + timedelta(days=2),
        price_minor=100,
        prize_minor=5000,
        status=status,
    )


class ClientCatalogViewTests(TestCase):
    def setUp(self):
        self.user = create_user(
            username="catalog_client",
            email="catalog.client@example.test",
            document="CATALOG-CLIENT",
            roles=(CLIENT,),
        )
        self.vendor = create_user(
            username="catalog_vendor",
            email="catalog.vendor@example.test",
            document="CATALOG-VENDOR",
            roles=(VENDOR,),
        )
        self.product = make_product()

    def activate(self, user, mode):
        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = mode
        session.save()

    def test_catalog_only_lists_visible_events(self):
        visible = make_event(
            self.product,
            "Visible",
            DrawEvent.Status.SALES_OPEN,
        )
        make_event(
            self.product,
            "Borrador oculto",
            DrawEvent.Status.DRAFT,
        )
        self.activate(self.user, CLIENT)

        response = self.client.get(reverse("lottery:client_event_list"))

        self.assertContains(response, visible.name)
        self.assertNotContains(response, "Borrador oculto")

    def test_detail_exposes_purchase_form_when_open(self):
        event = make_event(
            self.product,
            "Detalle",
            DrawEvent.Status.SALES_OPEN,
        )
        self.activate(self.user, CLIENT)

        response = self.client.get(
            reverse(
                "lottery:client_event_detail",
                kwargs={"pk": event.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Comprar boleto")
        self.assertContains(response, "Confirmar compra")
        self.assertContains(response, "lottery-event-card--open")
        self.assertContains(response, 'id="id_position_1"')
        self.assertContains(response, 'id="id_position_4"')
        self.assertNotContains(response, 'placeholder="4 símbolos únicos"')

    def test_vendor_mode_is_forbidden(self):
        self.activate(self.vendor, VENDOR)

        response = self.client.get(reverse("lottery:client_event_list"))

        self.assertEqual(response.status_code, 403)

    def test_ticket_detail_only_allows_owner(self):
        event = make_event(
            self.product,
            "Boletos",
            DrawEvent.Status.SALES_OPEN,
        )
        own = Ticket.objects.create(
            user=self.user,
            event=event,
            normalized_key="0123",
            price_minor=100,
        )
        other_user = create_user(
            username="other_client",
            email="other.client@example.test",
            document="OTHER-CLIENT",
            roles=(CLIENT,),
        )
        other = Ticket.objects.create(
            user=other_user,
            event=event,
            normalized_key="4567",
            price_minor=100,
        )
        self.activate(self.user, CLIENT)

        response = self.client.get(reverse("lottery:client_ticket_list"))

        self.assertContains(response, "0123")
        self.assertNotContains(response, "4567")
        self.assertEqual(
            self.client.get(
                reverse(
                    "lottery:client_ticket_detail",
                    kwargs={"pk": own.pk},
                )
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse(
                    "lottery:client_ticket_detail",
                    kwargs={"pk": other.pk},
                )
            ).status_code,
            404,
        )

    def test_navigation_has_catalog_and_tickets(self):
        self.activate(self.user, CLIENT)

        response = self.client.get(reverse("lottery:client_event_list"))

        self.assertContains(response, "Sorteos")
        self.assertContains(response, "Mis boletos")

    def test_manual_open_is_available_before_planned_opening(self):
        now = timezone.now()
        event = DrawEvent.objects.create(
            product=self.product,
            name="Venta abierta manualmente",
            sales_open_at=now + timedelta(hours=2),
            draw_at=now + timedelta(hours=5),
            price_minor=100,
            prize_minor=5000,
            status=DrawEvent.Status.SALES_OPEN,
        )
        self.activate(self.user, CLIENT)

        response = self.client.get(
            reverse(
                "lottery:client_event_detail",
                kwargs={"pk": event.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_open_now"])
        self.assertContains(response, "Confirmar compra")

    def test_catalog_renders_open_and_upcoming_cards_with_state_colors(self):
        now = timezone.now()
        open_event = DrawEvent.objects.create(
            product=self.product,
            name="Abierto con borde verde",
            sales_open_at=now - timedelta(hours=1),
            draw_at=now + timedelta(hours=2),
            price_minor=100,
            prize_minor=5000,
            status=DrawEvent.Status.SALES_OPEN,
        )
        upcoming_event = DrawEvent.objects.create(
            product=self.product,
            name="Próximo con borde celeste",
            sales_open_at=now + timedelta(hours=3),
            draw_at=now + timedelta(hours=6),
            price_minor=100,
            prize_minor=5000,
            status=DrawEvent.Status.SCHEDULED,
        )
        self.activate(self.user, CLIENT)

        response = self.client.get(reverse("lottery:client_event_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, open_event.name)
        self.assertContains(response, upcoming_event.name)
        self.assertContains(response, "lottery-event-card--open")
        self.assertContains(response, "lottery-event-card--upcoming")
        self.assertContains(response, "Ventas abiertas")
        self.assertContains(response, "Próximamente")
        self.assertContains(response, "lottery-symbol-badge")

    def test_upcoming_detail_renders_without_template_syntax_error(self):
        now = timezone.now()
        event = DrawEvent.objects.create(
            product=self.product,
            name="Detalle próximo",
            sales_open_at=now + timedelta(hours=2),
            draw_at=now + timedelta(hours=5),
            price_minor=100,
            prize_minor=5000,
            status=DrawEvent.Status.SCHEDULED,
        )
        self.activate(self.user, CLIENT)

        response = self.client.get(
            reverse(
                "lottery:client_event_detail",
                kwargs={"pk": event.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "lottery-event-card--upcoming")
        self.assertContains(response, "Próximamente")
        self.assertContains(response, "Las ventas todavía no han iniciado.")
        self.assertNotContains(response, "Confirmar compra")

    def test_client_dashboard_prioritizes_open_events_before_upcoming(self):
        now = timezone.now()
        upcoming_event = DrawEvent.objects.create(
            product=self.product,
            name="Próximo primero por fecha",
            sales_open_at=now + timedelta(minutes=30),
            draw_at=now + timedelta(hours=1),
            price_minor=100,
            prize_minor=5000,
            status=DrawEvent.Status.SCHEDULED,
        )
        open_event = DrawEvent.objects.create(
            product=self.product,
            name="Abierto prioritario",
            sales_open_at=now - timedelta(hours=1),
            draw_at=now + timedelta(hours=3),
            price_minor=100,
            prize_minor=5000,
            status=DrawEvent.Status.SALES_OPEN,
        )
        self.activate(self.user, CLIENT)

        response = self.client.get(reverse("core:client_dashboard"))

        self.assertEqual(response.status_code, 200)
        rows = response.context["available_events"]
        self.assertEqual(rows[0]["event"], open_event)
        self.assertIn(upcoming_event, [row["event"] for row in rows])
        self.assertContains(response, "lottery-event-card--open")
        self.assertContains(response, "lottery-event-card--upcoming")
