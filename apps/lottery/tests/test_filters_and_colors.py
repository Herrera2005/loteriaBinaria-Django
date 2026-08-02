from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import ADMINISTRATOR, CLIENT
from apps.accounts.tests.factories import create_user
from apps.lottery.forms import LotteryProductForm
from apps.lottery.models import DrawEvent, LotteryProduct


def create_product(*, code, name, color):
    product = LotteryProduct(
        kind=LotteryProduct.Kind.CUSTOM,
        code=code,
        name=name,
        allowed_symbols="A|B|C|D",
        selection_count=3,
        accent_color=color,
        is_active=True,
    )
    product.full_clean()
    product.save()
    return product


def create_event(*, product, name, close_in_hours, price=100, prize=5000):
    now = timezone.now()
    draw_at = now + timedelta(hours=close_in_hours, minutes=10)
    return DrawEvent.objects.create(
        product=product,
        name=name,
        sales_open_at=now - timedelta(hours=1),
        draw_at=draw_at,
        price_minor=price,
        prize_minor=prize,
        status=DrawEvent.Status.SALES_OPEN,
    )


class ProductColorTests(TestCase):
    def test_valid_color_is_normalized_and_saved(self):
        product = create_product(
            code="COLOR_A",
            name="Color A",
            color="#1a2b3c",
        )
        self.assertEqual(product.accent_color, "#1A2B3C")

    def test_invalid_css_value_is_rejected(self):
        product = LotteryProduct(
            kind=LotteryProduct.Kind.CUSTOM,
            code="COLOR_BAD",
            name="Color inválido",
            allowed_symbols="A|B|C",
            selection_count=2,
            accent_color="red;display:none",
        )
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_form_uses_color_input(self):
        form = LotteryProductForm()

        accent_widget = form.fields["accent_color"].widget

        self.assertEqual(
            accent_widget.input_type,
            "color",
        )
        self.assertIn(
            "form-control-color",
            accent_widget.attrs.get("class", ""),
        )

    def test_color_remains_editable_when_product_has_events(self):
        product = create_product(
            code="COLOR_EVT",
            name="Con evento",
            color="#124578",
        )
        create_event(
            product=product,
            name="Evento",
            close_in_hours=3,
        )

        form = LotteryProductForm(instance=product)

        self.assertFalse(form.fields["accent_color"].disabled)

    def test_missing_color_keeps_existing_value_on_legacy_edit(self):
        product = create_product(
            code="COLOR_KEEP",
            name="Con color existente",
            color="#124578",
        )
        create_event(
            product=product,
            name="Evento",
            close_in_hours=3,
        )
        form = LotteryProductForm(
            data={
                "name": "Nombre actualizado",
                "is_active": "on",
            },
            instance=product,
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        saved = form.save()
        self.assertEqual(saved.accent_color, "#124578")


class EventOrderingTests(TestCase):
    def setUp(self):
        self.product = create_product(code="ORDEN", name="Orden", color="#0D6EFD")
        self.admin = create_user(
            username="ordering_admin",
            email="ordering-admin@example.test",
            document="ORDER-ADMIN",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        self.client_user = create_user(
            username="ordering_client",
            email="ordering-client@example.test",
            document="ORDER-CLIENT",
            roles=(CLIENT,),
        )

    def activate(self, user, mode):
        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = mode
        session.save()

    def test_admin_default_order_is_nearest_close(self):
        later = create_event(product=self.product, name="Cierra después", close_in_hours=4)
        sooner = create_event(product=self.product, name="Cierra primero", close_in_hours=1)
        self.activate(self.admin, ADMINISTRATOR)
        response = self.client.get(reverse("lottery:event_list"))
        self.assertEqual(list(response.context["events"])[:2], [sooner, later])
        self.assertEqual(response.context["selected_order"], "close_asc")

    def test_admin_can_order_by_farthest_draw(self):
        sooner = create_event(product=self.product, name="Sorteo cercano", close_in_hours=1)
        later = create_event(product=self.product, name="Sorteo lejano", close_in_hours=4)
        self.activate(self.admin, ADMINISTRATOR)
        response = self.client.get(reverse("lottery:event_list"), {"order": "draw_desc"})
        self.assertEqual(list(response.context["events"])[:2], [later, sooner])

    def test_client_can_order_by_price_and_sees_color(self):
        expensive = create_event(product=self.product, name="Caro", close_in_hours=2, price=500)
        cheap = create_event(product=self.product, name="Barato", close_in_hours=3, price=100)
        self.activate(self.client_user, CLIENT)
        response = self.client.get(reverse("lottery:client_event_list"), {"order": "price_asc"})
        self.assertEqual(list(response.context["events"])[:2], [cheap, expensive])
        self.assertContains(response, self.product.accent_color)
        self.assertContains(response, "Precio menor")

    def test_invalid_order_falls_back_to_safe_default(self):
        create_event(product=self.product, name="Evento", close_in_hours=2)
        self.activate(self.client_user, CLIENT)
        response = self.client.get(reverse("lottery:client_event_list"), {"order": "__unsafe__"})
        self.assertEqual(response.context["selected_order"], "close_asc")
