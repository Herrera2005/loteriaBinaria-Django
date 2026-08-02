"""Pruebas de formularios del CRUD evaluable de lottery."""

from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.lottery.forms import DrawEventForm, LotteryProductForm
from apps.lottery.models import DrawEvent, LotteryProduct
from apps.lottery.tests.test_models import create_event, create_product


class LotteryProductFormTests(TestCase):
    def test_valid_hexadecimal_product(self):
        form = LotteryProductForm(
            data={
                "code": LotteryProduct.Code.HEXADECIMAL,
                "name": "Hexadecimal",
                "allowed_symbols": "0123456789ABCDEF",
                "selection_count": 6,
                "is_active": True,
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_hexadecimal_with_four_symbols_is_invalid(self):
        form = LotteryProductForm(
            data={
                "code": LotteryProduct.Code.HEXADECIMAL,
                "name": "Hexadecimal",
                "allowed_symbols": "0123456789ABCDEF",
                "selection_count": 4,
                "is_active": True,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("selection_count", form.errors)

    def test_product_widgets_use_bootstrap(self):
        form = LotteryProductForm()

        self.assertIn(
            "form-control",
            form.fields["code"].widget.attrs["class"],
        )
        self.assertIn(
            "form-select",
            form.fields["product_type"].widget.attrs["class"],
        )
        self.assertIn(
            "form-control",
            form.fields["name"].widget.attrs["class"],
        )
        self.assertIn(
            "form-check-input",
            form.fields["is_active"].widget.attrs["class"],
        )

    def test_configuration_is_disabled_when_events_exist(self):
        product = create_product()
        create_event(product=product)

        form = LotteryProductForm(instance=product)

        self.assertTrue(form.fields["code"].disabled)
        self.assertTrue(form.fields["allowed_symbols"].disabled)
        self.assertTrue(form.fields["selection_count"].disabled)


class DrawEventFormTests(TestCase):
    def valid_data(self, product):
        draw_at = timezone.now() + timedelta(days=2)
        return {
            "product": product.pk,
            "name": "Sorteo formulario",
            "sales_open_at": (
                timezone.now() + timedelta(hours=1)
            ).strftime("%Y-%m-%dT%H:%M"),
            "draw_at": draw_at.strftime("%Y-%m-%dT%H:%M"),
            "price_minor": 100,
            "prize_minor": 5000,
        }

    def test_form_calculates_close_ten_minutes_before_draw(self):
        product = create_product()
        form = DrawEventForm(data=self.valid_data(product))

        self.assertTrue(form.is_valid(), form.errors.as_json())
        event = form.save()

        self.assertEqual(
            event.sales_close_at,
            event.draw_at - timedelta(minutes=10),
        )

    def test_money_inputs_are_always_converted_from_dollars_to_minor_units(self):
        product = create_product()
        data = self.valid_data(product)
        data["price_minor"] = "1.50"
        data["prize_minor"] = "10.00"

        form = DrawEventForm(data=data)

        self.assertTrue(form.is_valid(), form.errors.as_json())
        event = form.save()
        self.assertEqual(event.price_minor, 150)
        self.assertEqual(event.prize_minor, 1000)

    def test_existing_draft_money_is_converted_from_dollars_to_minor_units(self):
        event = create_event(status=DrawEvent.Status.DRAFT)
        data = self.valid_data(event.product)
        data["name"] = "Borrador actualizado"
        data["price_minor"] = "2.75"
        data["prize_minor"] = "25.00"

        form = DrawEventForm(data=data, instance=event)

        self.assertTrue(form.is_valid(), form.errors.as_json())
        updated = form.save()
        self.assertEqual(updated.price_minor, 275)
        self.assertEqual(updated.prize_minor, 2500)
        self.assertEqual(updated.status, DrawEvent.Status.DRAFT)

    def test_form_rejects_opening_after_calculated_close(self):
        product = create_product()
        data = self.valid_data(product)
        draw_at = timezone.now() + timedelta(hours=1)
        data["draw_at"] = draw_at.strftime("%Y-%m-%dT%H:%M")
        data["sales_open_at"] = (
            draw_at - timedelta(minutes=5)
        ).strftime("%Y-%m-%dT%H:%M")

        form = DrawEventForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("sales_open_at", form.errors)

    def test_event_form_does_not_expose_transition_fields(self):
        form = DrawEventForm()

        self.assertNotIn("status", form.fields)
        self.assertNotIn("cancellation_reason", form.fields)

    def test_non_draft_event_protects_critical_fields(self):
        event = create_event(status=DrawEvent.Status.PUBLISHED)

        form = DrawEventForm(instance=event)

        for field_name in (
            "product",
            "sales_open_at",
            "draw_at",
            "price_minor",
            "prize_minor",
        ):
            with self.subTest(field_name=field_name):
                self.assertTrue(form.fields[field_name].disabled)

        self.assertNotIn("status", form.fields)
        self.assertNotIn("cancellation_reason", form.fields)

    def test_event_widgets_use_bootstrap(self):
        form = DrawEventForm()

        self.assertIn(
            "form-select",
            form.fields["product"].widget.attrs["class"],
        )
        self.assertIn(
            "form-control",
            form.fields["draw_at"].widget.attrs["class"],
        )
        self.assertIn(
            "form-control",
            form.fields["price_minor"].widget.attrs["class"],
        )

        self.assertNotIn("status", form.fields)
        self.assertNotIn("cancellation_reason", form.fields)

    def test_ticket_and_result_forms_do_not_exist(self):
        from apps.lottery import forms as lottery_forms

        self.assertFalse(hasattr(lottery_forms, "TicketForm"))
        self.assertFalse(hasattr(lottery_forms, "DrawResultForm"))
