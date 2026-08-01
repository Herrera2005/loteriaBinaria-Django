from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.seed import ensure_legal_versions, ensure_role_groups


class Command(BaseCommand):
    help = "Crea roles y versiones legales mínimas de forma idempotente."

    @transaction.atomic
    def handle(self, *args, **options):
        groups = ensure_role_groups()
        terms = ensure_legal_versions()
        self.stdout.write(
            self.style.SUCCESS(
                f"Baseline lista: {len(groups)} roles y {len(terms)} versiones legales."
            )
        )
