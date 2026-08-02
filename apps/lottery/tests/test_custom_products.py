"""Pruebas P-35B-R2 para productos personalizados tokenizados."""

from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.test import TestCase

from apps.lottery.forms import LotteryProductForm
from apps.lottery.models import LotteryProduct
from apps.lottery.tests.test_models import create_event, create_product


def manual_product_data(*, code, name, tokens, selection_count):
    data = QueryDict("", mutable=True)
    data.update(
        {
            "product_type": LotteryProduct.Kind.CUSTOM,
            "code": code,
            "name": name,
            "symbol_mode": "MANUAL",
            "selection_count": str(selection_count),
            "is_active": "on",
        }
    )
    data.setlist("symbol_token", tokens)
    return data


class CustomLotteryProductTests(TestCase):
    def test_manual_custom_product_uses_individual_tokens(self):
        form = LotteryProductForm(
            data=manual_product_data(
                code="LETRAS_5",
                name="Sorteo de letras",
                tokens=list("ABCDEFGH"),
                selection_count=5,
            )
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        product = form.save()

        self.assertEqual(product.kind, LotteryProduct.Kind.CUSTOM)
        self.assertEqual(product.code, "LETRAS_5")
        self.assertEqual(product.allowed_symbols, "A|B|C|D|E|F|G|H")
        self.assertEqual(product.symbol_tokens, tuple("ABCDEFGH"))
        self.assertEqual(product.selection_count, 5)

    def test_manual_product_accepts_two_character_token(self):
        form = LotteryProductForm(
            data=manual_product_data(
                code="DOBLE",
                name="Tokens dobles",
                tokens=["1", "2", "10", "A1"],
                selection_count=3,
            )
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        product = form.save()
        self.assertEqual(product.symbol_tokens, ("1", "2", "10", "A1"))

    def test_numeric_range_builds_individual_tokens(self):
        form = LotteryProductForm(
            data={
                "product_type": LotteryProduct.Kind.CUSTOM,
                "code": "RANGO_2_12",
                "name": "Rango numérico",
                "symbol_mode": "NUMERIC_RANGE",
                "range_start": "2",
                "range_end": "12",
                "selection_count": 4,
                "is_active": True,
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        product = form.save()
        self.assertEqual(
            product.symbol_tokens,
            ("2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"),
        )

    def test_letter_range_builds_symbols(self):
        form = LotteryProductForm(
            data={
                "product_type": LotteryProduct.Kind.CUSTOM,
                "code": "LETRAS_AF",
                "name": "Letras A-F",
                "symbol_mode": "LETTER_RANGE",
                "range_start": "a",
                "range_end": "f",
                "selection_count": 3,
                "is_active": True,
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.save().symbol_tokens, tuple("ABCDEF"))

    def test_code_and_symbols_are_normalized_to_uppercase(self):
        form = LotteryProductForm(
            data=manual_product_data(
                code="mixto_abc123",
                name="Mixto",
                tokens=["a", "b1", "2"],
                selection_count=3,
            )
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        product = form.save()
        self.assertEqual(product.code, "MIXTO_ABC123")
        self.assertEqual(product.symbol_tokens, ("A", "B1", "2"))

    def test_repeated_symbols_are_rejected(self):
        form = LotteryProductForm(
            data=manual_product_data(
                code="REPETIDOS",
                name="Repetidos",
                tokens=["A", "A", "B"],
                selection_count=2,
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("allowed_symbols", form.errors)

    def test_selection_cannot_exceed_symbol_universe(self):
        product = LotteryProduct(
            kind=LotteryProduct.Kind.CUSTOM,
            code="POCOS",
            name="Pocos símbolos",
            allowed_symbols="A|B|C",
            selection_count=4,
        )

        with self.assertRaises(ValidationError) as context:
            product.full_clean()

        self.assertIn("selection_count", context.exception.message_dict)

    def test_selection_maximum_is_eight(self):
        product = LotteryProduct(
            kind=LotteryProduct.Kind.CUSTOM,
            code="NUEVE",
            name="Nueve posiciones",
            allowed_symbols="A|B|C|D|E|F|G|H|I",
            selection_count=9,
        )

        with self.assertRaises(ValidationError) as context:
            product.full_clean()

        self.assertIn("selection_count", context.exception.message_dict)

    def test_product_with_events_keeps_structural_configuration(self):
        product = create_product()
        create_event(product=product)
        product.kind = LotteryProduct.Kind.CUSTOM
        product.code = "CAMBIADO"
        product.allowed_symbols = "A|B|C|D"
        product.selection_count = 3

        with self.assertRaises(ValidationError):
            product.save()
