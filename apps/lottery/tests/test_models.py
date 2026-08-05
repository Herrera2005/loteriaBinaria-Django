"""Pruebas de validación de los modelos de lottery."""

from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.test import TestCase
from django.utils import timezone

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
    *,
    code=LotteryProduct.Code.OCTAL,
):
    rule = LotteryProduct.PRODUCT_RULES[code]
    product = LotteryProduct(
        code=code,
        name=dict(LotteryProduct.Code.choices)[code],
        allowed_symbols=rule["allowed_symbols"],
        selection_count=rule["selection_count"],
    )
    product.full_clean()
    product.save()
    return product


def create_event(*, product=None, status=DrawEvent.Status.DRAFT):
    product = product or create_product()
    draw_at = timezone.now() + timedelta(days=2)
    event = DrawEvent(
        product=product,
        name="Sorteo de prueba",
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


def create_client():
    return create_user(
        username="cliente_lottery",
        email="cliente-lottery@example.test",
        document="CLI-LOT-001",
        roles=(CLIENT,),
    )


def create_admin():
    return create_user(
        username="admin_lottery",
        email="admin-lottery@example.test",
        document="ADM-LOT-001",
        roles=(ADMINISTRATOR,),
        is_staff=True,
    )


class LotteryProductModelTests(TestCase):
    def test_official_product_rules_are_exact(self):
        expected = {
            LotteryProduct.Code.OCTAL: ("01234567", 4),
            LotteryProduct.Code.DECIMAL: ("0123456789", 5),
            LotteryProduct.Code.HEXADECIMAL: (
                "0123456789ABCDEF",
                6,
            ),
        }

        for code, (symbols, count) in expected.items():
            with self.subTest(code=code):
                rule = LotteryProduct.PRODUCT_RULES[code]
                self.assertEqual(rule["allowed_symbols"], symbols)
                self.assertEqual(rule["selection_count"], count)

    def test_hexadecimal_rejects_four_symbols(self):
        product = LotteryProduct(
            code=LotteryProduct.Code.HEXADECIMAL,
            name="Hexadecimal",
            allowed_symbols="0123456789ABCDEF",
            selection_count=4,
        )

        with self.assertRaises(ValidationError) as context:
            product.full_clean()

        self.assertIn(
            "selection_count",
            context.exception.message_dict,
        )

    def test_octal_rejects_wrong_allowed_symbols(self):
        product = LotteryProduct(
            code=LotteryProduct.Code.OCTAL,
            name="Octal",
            allowed_symbols="0123456789",
            selection_count=4,
        )

        with self.assertRaises(ValidationError) as context:
            product.full_clean()

        self.assertIn(
            "allowed_symbols",
            context.exception.message_dict,
        )

    def test_code_is_unique(self):
        create_product(code=LotteryProduct.Code.DECIMAL)

        with self.assertRaises(IntegrityError), transaction.atomic():
            LotteryProduct.objects.create(
                code=LotteryProduct.Code.DECIMAL,
                name="Otro decimal",
                allowed_symbols="0123456789",
                selection_count=5,
            )


    def test_product_with_events_rejects_configuration_change(self):
        product = create_product()
        create_event(product=product)
        product.code = LotteryProduct.Code.DECIMAL
        product.allowed_symbols = "0123456789"
        product.selection_count = 5

        with self.assertRaises(ValidationError):
            product.save()

    def test_product_configuration_rejects_bulk_update(self):
        product = create_product()

        with self.assertRaises(ValidationError):
            LotteryProduct.objects.filter(pk=product.pk).update(
                selection_count=5
            )


class DrawEventModelTests(TestCase):
    def test_close_is_exactly_ten_minutes_before_draw(self):
        event = create_event()

        self.assertEqual(
            event.sales_close_at,
            event.draw_at - timedelta(minutes=10),
        )

    def test_save_recalculates_close_from_draw_time(self):
        product = create_product()
        draw_at = timezone.now() + timedelta(days=1)
        event = DrawEvent(
            product=product,
            name="Cierre automático",
            sales_open_at=timezone.now() + timedelta(hours=1),
            sales_close_at=timezone.now(),
            draw_at=draw_at,
            price_minor=100,
            prize_minor=1000,
        )

        event.save()

        self.assertEqual(
            event.sales_close_at,
            draw_at - timedelta(minutes=10),
        )

    def test_opening_must_be_before_calculated_close(self):
        product = create_product()
        draw_at = timezone.now() + timedelta(hours=1)
        event = DrawEvent(
            product=product,
            name="Apertura inválida",
            sales_open_at=draw_at - timedelta(minutes=5),
            sales_close_at=draw_at - DRAW_CLOSE_OFFSET,
            draw_at=draw_at,
            price_minor=100,
            prize_minor=1000,
        )

        with self.assertRaises(ValidationError) as context:
            event.full_clean()

        self.assertIn(
            "sales_open_at",
            context.exception.message_dict,
        )

    def test_price_and_prize_are_big_integer_fields(self):
        price_field = DrawEvent._meta.get_field("price_minor")
        prize_field = DrawEvent._meta.get_field("prize_minor")

        self.assertIsInstance(price_field, models.BigIntegerField)
        self.assertIsInstance(prize_field, models.BigIntegerField)
        self.assertNotIsInstance(price_field, models.FloatField)
        self.assertNotIsInstance(prize_field, models.FloatField)

    def test_cancelled_event_requires_reason(self):
        event = create_event()
        event.status = DrawEvent.Status.CANCELLED
        event.cancellation_reason = ""

        with self.assertRaises(ValidationError) as context:
            event.full_clean()

        self.assertIn(
            "cancellation_reason",
            context.exception.message_dict,
        )

    def test_product_relation_uses_protect(self):
        field = DrawEvent._meta.get_field("product")
        self.assertIs(field.remote_field.on_delete, models.PROTECT)

        product = create_product()
        create_event(product=product)
        with self.assertRaises(models.ProtectedError):
            product.delete()


    def test_published_event_rejects_direct_critical_change(self):
        event = create_event(status=DrawEvent.Status.PUBLISHED)
        event.price_minor += 1

        with self.assertRaises(ValidationError):
            event.save()

    def test_published_event_rejects_direct_status_change(self):
        event = create_event(status=DrawEvent.Status.PUBLISHED)
        event.status = DrawEvent.Status.SALES_OPEN

        with self.assertRaises(ValidationError):
            event.save()

    def test_event_rejects_bulk_critical_or_status_update(self):
        event = create_event(status=DrawEvent.Status.PUBLISHED)

        with self.assertRaises(ValidationError):
            DrawEvent.objects.filter(pk=event.pk).update(price_minor=999)

        with self.assertRaises(ValidationError):
            DrawEvent.objects.filter(pk=event.pk).update(
                status=DrawEvent.Status.DRAFT
            )


class TicketModelTests(TestCase):
    def test_ticket_normalizes_uppercase_and_validates_key(self):
        event = create_event(
            product=create_product(
                code=LotteryProduct.Code.HEXADECIMAL
            )
        )
        ticket = Ticket(
            user=create_client(),
            event=event,
            normalized_key="ab12ef",
            price_minor=event.price_minor,
        )

        ticket.full_clean()
        ticket.save()

        self.assertEqual(ticket.normalized_key, "12ABEF")

    def test_ticket_rejects_repeated_symbols(self):
        event = create_event()
        ticket = Ticket(
            user=create_client(),
            event=event,
            normalized_key="0012",
            price_minor=event.price_minor,
        )

        with self.assertRaises(ValidationError) as context:
            ticket.full_clean()

        self.assertIn(
            "normalized_key",
            context.exception.message_dict,
        )

    def test_ticket_rejects_invalid_symbol(self):
        event = create_event()
        ticket = Ticket(
            user=create_client(),
            event=event,
            normalized_key="0187",
            price_minor=event.price_minor,
        )

        with self.assertRaises(ValidationError) as context:
            ticket.full_clean()

        self.assertIn(
            "normalized_key",
            context.exception.message_dict,
        )

    def test_ticket_is_unique_per_event_and_key(self):
        event = create_event()
        user = create_client()

        Ticket.objects.create(
            user=user,
            event=event,
            normalized_key="0123",
            price_minor=event.price_minor,
        )

        second_user = create_user(
            username="cliente_lottery_2",
            email="cliente-lottery-2@example.test",
            document="CLI-LOT-002",
            roles=(CLIENT,),
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Ticket.objects.create(
                user=second_user,
                event=event,
                normalized_key="0123",
                price_minor=event.price_minor,
            )

    def test_ticket_permutations_share_the_same_canonical_key(self):
        event = create_event()
        first_user = create_client()
        second_user = create_user(
            username="cliente_permutation",
            email="cliente-permutation@example.test",
            document="CLI-PERM-002",
            roles=(CLIENT,),
        )

        first = Ticket.objects.create(
            user=first_user,
            event=event,
            normalized_key="3210",
            price_minor=event.price_minor,
        )
        self.assertEqual(first.normalized_key, "0123")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Ticket.objects.create(
                user=second_user,
                event=event,
                normalized_key="0123",
                price_minor=event.price_minor,
            )

    def test_ticket_relations_use_protect(self):
        self.assertIs(
            Ticket._meta.get_field("user").remote_field.on_delete,
            models.PROTECT,
        )
        self.assertIs(
            Ticket._meta.get_field("event").remote_field.on_delete,
            models.PROTECT,
        )

    def test_ticket_cannot_be_deleted(self):
        event = create_event()
        ticket = Ticket.objects.create(
            user=create_client(),
            event=event,
            normalized_key="0123",
            price_minor=event.price_minor,
        )

        with self.assertRaises(ValidationError):
            ticket.delete()

        with self.assertRaises(ValidationError):
            Ticket.objects.filter(pk=ticket.pk).delete()


class DrawResultModelTests(TestCase):
    def test_result_is_one_to_one_and_protected(self):
        field = DrawResult._meta.get_field("event")

        self.assertTrue(field.one_to_one)
        self.assertIs(field.remote_field.on_delete, models.PROTECT)

    def test_result_validates_winning_key(self):
        event = create_event(
            product=create_product(
                code=LotteryProduct.Code.DECIMAL
            )
        )
        result = DrawResult(
            event=event,
            winning_key="01234",
            published_by=create_admin(),
            reason="Resultado académico verificado.",
        )

        result.full_clean()
        result.save()

        self.assertEqual(result.winning_key, "01234")

    def test_result_rejects_repeated_symbols(self):
        event = create_event()
        result = DrawResult(
            event=event,
            winning_key="0012",
            published_by=create_admin(),
            reason="Intento inválido.",
        )

        with self.assertRaises(ValidationError) as context:
            result.full_clean()

        self.assertIn(
            "winning_key",
            context.exception.message_dict,
        )

    def test_only_one_result_per_event(self):
        event = create_event()
        DrawResult.objects.create(
            event=event,
            winning_key="0123",
            published_by=create_admin(),
            reason="Primer resultado.",
        )

        another_admin = create_user(
            username="admin_lottery_2",
            email="admin-lottery-2@example.test",
            document="ADM-LOT-002",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            DrawResult.objects.create(
                event=event,
                winning_key="4567",
                published_by=another_admin,
                reason="Segundo resultado no permitido.",
            )

    def test_result_cannot_be_updated_or_deleted(self):
        result = DrawResult.objects.create(
            event=create_event(),
            winning_key="0123",
            published_by=create_admin(),
            reason="Resultado inicial.",
        )

        result.winning_key = "4567"
        with self.assertRaises(ValidationError):
            result.save()

        with self.assertRaises(ValidationError):
            DrawResult.objects.filter(pk=result.pk).update(
                winning_key="4567"
            )

        with self.assertRaises(ValidationError):
            result.delete()
