from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.lottery.models import DrawEvent, DrawResult, LotteryProduct


class PublicApiDemoSeedTests(TestCase):
    def test_seed_is_idempotent(self):
        output = StringIO()
        call_command("seed_public_api_demo", stdout=output)
        first_counts = (
            LotteryProduct.objects.count(),
            DrawEvent.objects.count(),
            DrawResult.objects.count(),
        )
        call_command("seed_public_api_demo", stdout=output)
        second_counts = (
            LotteryProduct.objects.count(),
            DrawEvent.objects.count(),
            DrawResult.objects.count(),
        )
        self.assertEqual(first_counts, (3, 3, 1))
        self.assertEqual(second_counts, first_counts)
