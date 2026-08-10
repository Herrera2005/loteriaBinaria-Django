from __future__ import annotations

from django.test import SimpleTestCase

from apps.api.v1.money import money_data
from apps.finance.models import Wallet


class ApiV1MoneyContractTests(
    SimpleTestCase
):
    def test_real_money_contract(self):
        self.assertEqual(
            money_data(
                9000,
                currency=Wallet.Currency.REAL,
            ),
            {
                "minor": 9000,
                "currency": "REAL",
                "display": "$ 90.00",
            },
        )

    def test_virtual_money_contract(self):
        self.assertEqual(
            money_data(
                10000,
                currency=Wallet.Currency.VIRTUAL,
            ),
            {
                "minor": 10000,
                "currency": "VIRTUAL",
                "display": "V 100.00",
            },
        )

    def test_zero_is_formatted_correctly(self):
        self.assertEqual(
            money_data(
                0,
                currency=Wallet.Currency.REAL,
            ),
            {
                "minor": 0,
                "currency": "REAL",
                "display": "$ 0.00",
            },
        )

    def test_negative_amount_is_preserved(self):
        self.assertEqual(
            money_data(
                -250,
                currency=Wallet.Currency.VIRTUAL,
            ),
            {
                "minor": -250,
                "currency": "VIRTUAL",
                "display": "V -2.50",
            },
        )

    def test_unknown_currency_is_rejected(self):
        with self.assertRaises(ValueError):
            money_data(
                100,
                currency="BITCOIN",
            )