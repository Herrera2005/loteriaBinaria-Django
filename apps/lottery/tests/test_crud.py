"""Pruebas de permisos y reglas del CRUD visual de lottery."""

from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import ADMINISTRATOR, CLIENT
from apps.accounts.tests.factories import create_user
from apps.lottery.models import (
    DRAW_CLOSE_OFFSET,
    DrawEvent,
    DrawResult,
    LotteryProduct,
    Ticket,
)


def create_product(
    code=LotteryProduct.Code.OCTAL,
    name=None,
    is_active=True,
):
    rule = LotteryProduct.PRODUCT_RULES[code]
    product = LotteryProduct(
        code=code,
        name=name or dict(LotteryProduct.Code.choices)[code],
        allowed_symbols=rule["allowed_symbols"],
        selection_count=rule["selection_count"],
        is_active=is_active,
    )
    product.full_clean()
    product.save()
    return product


def create_event(
    product=None,
    name="Evento CRUD",
    status=DrawEvent.Status.DRAFT,
):
    product = product or create_product()
    draw_at = timezone.now() + timedelta(days=2)
    event = DrawEvent(
        product=product,
        name=name,
        sales_open_at=timezone.now() + timedelta(hours=1),
        sales_close_at=draw_at - DRAW_CLOSE_OFFSET,
        draw_at=draw_at,
        price_minor=100,
        prize_minor=5000,
        status=status,
    )
    event.full_clean()
    event.save()
    return event


class AdminModeTestCase(TestCase):
    def setUp(self):
        self.admin_user = create_user(
            username="admin_lottery_crud",
            email="admin-lottery-crud@example.test",
            document="ADM-LOT-CRUD",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        self.client.force_login(self.admin_user)

        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()


class AccessTests(TestCase):
    def test_anonymous_redirects_to_login(self):
        response = self.client.get(
            reverse("lottery:product_list")
        )
        self.assertEqual(response.status_code, 302)

    def test_client_mode_gets_403(self):
        user = create_user(
            username="cliente_lottery_crud",
            email="cliente-lottery-crud@example.test",
            document="CLI-LOT-CRUD",
            roles=(CLIENT,),
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("lottery:event_list")
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_can_open_all_get_views(self):
        admin = create_user(
            username="admin_lottery_access",
            email="admin-lottery-access@example.test",
            document="ADM-LOT-ACCESS",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        product = create_product()
        event = create_event(product=product)

        self.client.force_login(admin)

        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

        urls = (
            reverse("lottery:product_list"),
            reverse("lottery:product_create"),
            reverse(
                "lottery:product_detail",
                args=(product.pk,),
            ),
            reverse(
                "lottery:product_update",
                args=(product.pk,),
            ),
            reverse(
                "lottery:product_delete",
                args=(product.pk,),
            ),
            reverse("lottery:event_list"),
            reverse("lottery:event_create"),
            reverse(
                "lottery:event_detail",
                args=(event.pk,),
            ),
            reverse(
                "lottery:event_update",
                args=(event.pk,),
            ),
            reverse(
                "lottery:event_delete",
                args=(event.pk,),
            ),
        )

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    self.client.get(url).status_code,
                    200,
                )


class ProductCrudTests(AdminModeTestCase):
    def test_filter_and_create_product(self):
        active = create_product()

        inactive = create_product(
            code=LotteryProduct.Code.DECIMAL,
            is_active=False,
        )

        response = self.client.get(
            reverse("lottery:product_list"),
            {"active": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, active.name)

        products = list(response.context["products"])

        self.assertIn(active, products)
        self.assertNotIn(inactive, products)

        create_response = self.client.post(
            reverse("lottery:product_create"),
            {
                "code": LotteryProduct.Code.HEXADECIMAL,
                "name": "Hexadecimal",
                "allowed_symbols": "0123456789ABCDEF",
                "selection_count": 6,
                "is_active": True,
            },
        )

        hexadecimal = LotteryProduct.objects.get(
            code=LotteryProduct.Code.HEXADECIMAL,
        )

        self.assertRedirects(
            create_response,
            reverse(
                "lottery:product_detail",
                args=(hexadecimal.pk,),
            ),
        )

    def test_delete_product_without_events(self):
        product = create_product()

        response = self.client.post(
            reverse(
                "lottery:product_delete",
                args=(product.pk,),
            )
        )

        self.assertRedirects(
            response,
            reverse("lottery:product_list"),
        )
        self.assertFalse(
            LotteryProduct.objects.filter(
                pk=product.pk,
            ).exists()
        )

    def test_product_with_events_is_not_deleted(self):
        product = create_product()
        create_event(product=product)

        response = self.client.post(
            reverse(
                "lottery:product_delete",
                args=(product.pk,),
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "lottery:product_detail",
                args=(product.pk,),
            ),
        )
        self.assertTrue(
            LotteryProduct.objects.filter(
                pk=product.pk,
            ).exists()
        )


class EventCrudTests(AdminModeTestCase):
    def valid_data(self, product):
        draw_at = timezone.now() + timedelta(days=3)

        return {
            "product": product.pk,
            "name": "Evento creado",
            "sales_open_at": (
                timezone.now() + timedelta(hours=1)
            ).strftime("%Y-%m-%dT%H:%M"),
            "draw_at": draw_at.strftime("%Y-%m-%dT%H:%M"),
            "price_minor": 100,
            "prize_minor": 5000,
            "status": DrawEvent.Status.DRAFT,
            "cancellation_reason": "",
        }

    def test_create_event_and_calculate_close(self):
        product = create_product()

        response = self.client.post(
            reverse("lottery:event_create"),
            self.valid_data(product),
        )

        event = DrawEvent.objects.get(
            name="Evento creado"
        )

        self.assertRedirects(
            response,
            reverse(
                "lottery:event_detail",
                args=(event.pk,),
            ),
        )
        self.assertEqual(
            event.sales_close_at,
            event.draw_at - timedelta(minutes=10),
        )

    def test_published_event_keeps_critical_fields(self):
        product = create_product()
        event = create_event(
            product=product,
            status=DrawEvent.Status.PUBLISHED,
        )

        original = (
            event.product_id,
            event.sales_open_at,
            event.draw_at,
            event.price_minor,
            event.prize_minor,
        )

        other = create_product(
            LotteryProduct.Code.DECIMAL
        )
        data = self.valid_data(other)
        data.update(
            {
                "name": "Nombre permitido",
                "status": DrawEvent.Status.SALES_OPEN,
                "price_minor": 999,
                "prize_minor": 999,
            }
        )

        response = self.client.post(
            reverse(
                "lottery:event_update",
                args=(event.pk,),
            ),
            data,
        )

        self.assertRedirects(
            response,
            reverse(
                "lottery:event_detail",
                args=(event.pk,),
            ),
        )

        event.refresh_from_db()

        self.assertEqual(
            event.name,
            "Nombre permitido",
        )
        self.assertEqual(
            (
                event.product_id,
                event.sales_open_at,
                event.draw_at,
                event.price_minor,
                event.prize_minor,
            ),
            original,
        )

    def test_draft_without_history_can_be_deleted(self):
        event = create_event()

        response = self.client.post(
            reverse(
                "lottery:event_delete",
                args=(event.pk,),
            )
        )

        self.assertRedirects(
            response,
            reverse("lottery:event_list"),
        )
        self.assertFalse(
            DrawEvent.objects.filter(
                pk=event.pk,
            ).exists()
        )

    def test_published_or_historical_event_cannot_be_deleted(self):
        published = create_event(
            status=DrawEvent.Status.PUBLISHED
        )

        self.client.post(
            reverse(
                "lottery:event_delete",
                args=(published.pk,),
            )
        )

        self.assertTrue(
            DrawEvent.objects.filter(
                pk=published.pk,
            ).exists()
        )

        draft = create_event(
            product=published.product,
            name="Con boleto",
        )

        client = create_user(
            username="cliente_ticket_crud",
            email="ticket@example.test",
            document="CLI-TICKET",
            roles=(CLIENT,),
        )

        Ticket.objects.create(
            user=client,
            event=draft,
            normalized_key="0123",
            price_minor=draft.price_minor,
        )

        self.client.post(
            reverse(
                "lottery:event_delete",
                args=(draft.pk,),
            )
        )

        self.assertTrue(
            DrawEvent.objects.filter(
                pk=draft.pk,
            ).exists()
        )

    def test_result_blocks_event_delete(self):
        event = create_event()

        DrawResult.objects.create(
            event=event,
            winning_key="0123",
            published_by=self.admin_user,
            reason="Resultado académico.",
        )

        self.client.post(
            reverse(
                "lottery:event_delete",
                args=(event.pk,),
            )
        )

        self.assertTrue(
            DrawEvent.objects.filter(
                pk=event.pk,
            ).exists()
        )

    def test_delete_requires_csrf(self):
        event = create_event()
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin_user)

        session = client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

        response = client.post(
            reverse(
                "lottery:event_delete",
                args=(event.pk,),
            )
        )

        self.assertEqual(response.status_code, 403)


class PaginationTests(AdminModeTestCase):
    def test_event_list_is_paginated(self):
        product = create_product()

        for index in range(16):
            create_event(
                product=product,
                name=f"Evento {index:02d}",
            )

        response = self.client.get(
            reverse("lottery:event_list")
        )

        self.assertTrue(
            response.context["is_paginated"]
        )
        self.assertEqual(
            len(response.context["events"]),
            15,
        )