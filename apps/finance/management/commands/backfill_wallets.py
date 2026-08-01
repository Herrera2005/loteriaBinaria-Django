"""Backfill idempotente de wallets para usuarios existentes."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.finance.models import Wallet
from apps.finance.services import ensure_user_wallets


class Command(BaseCommand):
    help = "Garantiza wallets REAL y VIRTUAL para todos los usuarios existentes."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        before = Wallet.objects.count()
        processed = 0

        for user in User.objects.order_by("pk").iterator():
            ensure_user_wallets(user)
            processed += 1

        created = Wallet.objects.count() - before
        self.stdout.write(
            self.style.SUCCESS(
                "Backfill completado: "
                f"{processed} usuario(s), {created} wallet(s) creada(s)."
            )
        )
