from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import CLIENT
from apps.accounts.tests.factories import create_user
from apps.core.date_utils import local_date_bounds
from apps.finance.models import Movement, Wallet


class MovementLocalDateFilterTests(TestCase):
    def test_movement_filter_uses_local_half_open_day(self):
        user = create_user(
            username="movement_date_client",
            email="movement-date-client@example.test",
            document="MOVEMENT-DATE",
            roles=(CLIENT,),
        )
        wallet = Wallet.objects.get(user=user, currency=Wallet.Currency.REAL)
        selected_day = timezone.localdate()
        start, end = local_date_bounds(selected_day)
        inside = Movement.objects.create(
            wallet=wallet,
            type=Movement.Type.TOP_UP,
            direction=Movement.Direction.CREDIT,
            amount_minor=100,
            balance_after_minor=100,
            description="INSIDE MOVEMENT DAY",
        )
        outside = Movement.objects.create(
            wallet=wallet,
            type=Movement.Type.TOP_UP,
            direction=Movement.Direction.CREDIT,
            amount_minor=100,
            balance_after_minor=200,
            description="OUTSIDE MOVEMENT DAY",
        )
        Movement._base_manager.filter(pk=inside.pk).update(
            created_at=start + timedelta(minutes=1)
        )
        Movement._base_manager.filter(pk=outside.pk).update(created_at=end)
        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = CLIENT
        session.save()

        response = self.client.get(
            reverse("finance:wallet_detail"),
            {
                "tab": "movements",
                "date_from": selected_day.isoformat(),
                "date_to": selected_day.isoformat(),
            },
        )

        self.assertContains(response, "INSIDE MOVEMENT DAY")
        self.assertNotContains(response, "OUTSIDE MOVEMENT DAY")
