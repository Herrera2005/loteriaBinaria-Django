from __future__ import annotations

import io
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import models
from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from apps.accounts.access import ACTIVE_MODE_SESSION_KEY
from apps.accounts.roles import ADMINISTRATOR, CLIENT, VENDOR
from apps.accounts.tests.factories import create_user
from apps.finance.models import Wallet
from apps.lottery.forms import DrawEventSeriesForm
from apps.lottery.models import (
    DrawEvent,
    DrawEventSeries,
    DrawEventStatusTransition,
    LotteryProduct,
)
from apps.lottery.services import (
    generate_series_events,
    process_active_event_series,
    purchase_ticket,
)


def make_product(*, code="OCTAL", active=True):
    rule = LotteryProduct.PRODUCT_RULES[code]
    return LotteryProduct.objects.create(
        kind=LotteryProduct.Kind.OFFICIAL,
        code=code,
        name=f"Producto {code}",
        allowed_symbols=rule["allowed_symbols"],
        selection_count=rule["selection_count"],
        is_active=active,
    )


def make_series(*, admin, product, name="Serie cierre", target=2):
    first_draw = timezone.now() + timedelta(hours=8)
    return DrawEventSeries.objects.create(
        name_prefix=name,
        product=product,
        first_draw_at=first_draw,
        next_draw_at=first_draw,
        recurrence_minutes=1440,
        sales_lead_minutes=480,
        price_minor=100,
        prize_minor=5000,
        future_events_target=target,
        created_by=admin,
    )


class ReadOnlyGetRegressionTests(TestCase):
    def setUp(self):
        self.admin = create_user(
            username="closure_admin",
            email="closure-admin@example.test",
            document="CLOSURE-ADMIN",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        self.client_user = create_user(
            username="closure_client",
            email="closure-client@example.test",
            document="CLOSURE-CLIENT",
            roles=(CLIENT,),
        )
        self.product = make_product()
        now = timezone.now()
        self.event = DrawEvent.objects.create(
            product=self.product,
            name="Evento listo para abrir",
            sales_open_at=now - timedelta(minutes=5),
            draw_at=now + timedelta(hours=2),
            price_minor=100,
            prize_minor=5000,
            status=DrawEvent.Status.SCHEDULED,
        )

    def _activate(self, user, mode):
        self.client.force_login(user)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = mode
        session.save()

    def _assert_get_does_not_sync(self, url):
        before_updated = self.event.updated_at
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, DrawEvent.Status.SCHEDULED)
        self.assertEqual(self.event.updated_at, before_updated)
        self.assertFalse(
            DrawEventStatusTransition.objects.filter(event=self.event).exists()
        )

    def test_administrator_event_list_get_does_not_write(self):
        self._activate(self.admin, ADMINISTRATOR)
        self._assert_get_does_not_sync(reverse("lottery:event_list"))

    def test_client_catalog_and_detail_get_do_not_write(self):
        self._activate(self.client_user, CLIENT)
        self._assert_get_does_not_sync(reverse("lottery:client_event_list"))
        self._assert_get_does_not_sync(
            reverse("lottery:client_event_detail", args=(self.event.pk,))
        )


class TransitionHistoryImmutabilityTests(TestCase):
    def setUp(self):
        admin = create_user(
            username="transition_admin",
            email="transition-admin@example.test",
            document="TRANSITION-ADMIN",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        product = make_product()
        event = DrawEvent.objects.create(
            product=product,
            name="Evento historial",
            sales_open_at=timezone.now() + timedelta(hours=1),
            draw_at=timezone.now() + timedelta(hours=3),
            price_minor=100,
            prize_minor=5000,
        )
        self.transition = DrawEventStatusTransition.objects.create(
            event=event,
            from_status=DrawEvent.Status.DRAFT,
            to_status=DrawEvent.Status.SCHEDULED,
            reason="Prueba de historial",
            changed_by=admin,
        )

    def test_queryset_update_delete_and_bulk_update_are_rejected(self):
        with self.assertRaises(ValidationError):
            DrawEventStatusTransition.objects.filter(
                pk=self.transition.pk
            ).update(reason="Manipulado")
        with self.assertRaises(ValidationError):
            DrawEventStatusTransition.objects.filter(
                pk=self.transition.pk
            ).delete()
        self.transition.reason = "Manipulado"
        with self.assertRaises(ValidationError):
            DrawEventStatusTransition.objects.bulk_update(
                [self.transition],
                ["reason"],
            )


class SeriesBatchAndObservabilityRegressionTests(TestCase):
    def setUp(self):
        self.admin = create_user(
            username="series_batch_admin",
            email="series-batch-admin@example.test",
            document="SERIES-BATCH-ADMIN",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        self.valid_product = make_product(code=LotteryProduct.Code.OCTAL)
        self.invalid_product = make_product(code=LotteryProduct.Code.DECIMAL)
        self.valid_series = make_series(
            admin=self.admin,
            product=self.valid_product,
            name="Serie válida",
        )
        self.invalid_series = make_series(
            admin=self.admin,
            product=self.invalid_product,
            name="Serie inválida",
        )
        self.invalid_product.is_active = False
        self.invalid_product.save(update_fields=("is_active", "updated_at"))

    def test_failed_attempt_persists_last_synced_at_without_partial_generation(self):
        attempted_at = timezone.now()
        with self.assertRaises(ValidationError):
            generate_series_events(
                series_id=self.invalid_series.pk,
                actor=self.admin,
                now=attempted_at,
            )
        self.invalid_series.refresh_from_db()
        self.assertEqual(self.invalid_series.last_synced_at, attempted_at)
        self.assertEqual(self.invalid_series.events.count(), 0)
        self.assertEqual(self.invalid_series.next_sequence, 1)

    def test_invalid_series_does_not_rollback_valid_series(self):
        batch = process_active_event_series(
            actor=self.admin,
            now=timezone.now(),
        )
        self.valid_series.refresh_from_db()
        self.invalid_series.refresh_from_db()
        self.assertEqual(self.valid_series.events.count(), 2)
        self.assertIsNotNone(self.valid_series.last_synced_at)
        self.assertIsNotNone(self.invalid_series.last_synced_at)
        self.assertEqual(len(batch.results), 1)
        self.assertEqual(len(batch.errors), 1)
        self.assertEqual(batch.errors[0].series_id, self.invalid_series.pk)

    def test_command_returns_failure_but_preserves_successful_series(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with self.assertRaises(CommandError):
            call_command(
                "process_lottery_schedules",
                stdout=stdout,
                stderr=stderr,
            )
        self.valid_series.refresh_from_db()
        self.assertEqual(self.valid_series.events.count(), 2)
        self.assertIn("errores=1", stdout.getvalue())
        self.assertIn(f"Serie {self.invalid_series.pk}", stderr.getvalue())

    def test_generated_events_use_only_targeted_state_sync(self):
        with patch(
            "apps.lottery.services.sync_lottery_event_states",
            return_value=0,
        ) as mocked_sync:
            result = generate_series_events(
                series_id=self.valid_series.pk,
                actor=self.admin,
            )
        mocked_sync.assert_called_once()
        self.assertEqual(
            tuple(mocked_sync.call_args.kwargs["event_ids"]),
            result.created_event_ids,
        )


class PortableConstraintAndSeriesRouteTests(TestCase):
    def setUp(self):
        self.admin = create_user(
            username="series_route_admin",
            email="series-route-admin@example.test",
            document="SERIES-ROUTE-ADMIN",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        self.product = make_product()
        self.series = make_series(admin=self.admin, product=self.product)
        self.client.force_login(self.admin)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

    def test_series_sequence_constraint_is_portable(self):
        constraint = next(
            item
            for item in DrawEvent._meta.constraints
            if isinstance(item, models.UniqueConstraint)
            and item.name == "lot_event_unique_series_sequence"
        )
        self.assertIsNone(constraint.condition)

    def test_dead_series_create_route_was_removed(self):
        with self.assertRaises(NoReverseMatch):
            reverse("lottery:series_create")

    def test_remaining_series_routes_are_reachable_and_method_safe(self):
        get_routes = (
            "lottery:series_list",
            "lottery:series_detail",
            "lottery:series_update",
            "lottery:series_archive",
        )
        for route in get_routes:
            with self.subTest(route=route):
                args = () if route == "lottery:series_list" else (self.series.pk,)
                self.assertEqual(self.client.get(reverse(route, args=args)).status_code, 200)

        for route in ("lottery:series_toggle", "lottery:series_generate"):
            with self.subTest(route=route):
                url = reverse(route, args=(self.series.pk,))
                self.assertEqual(self.client.get(url).status_code, 405)


class SeriesAndProductPaginationTests(TestCase):
    def setUp(self):
        self.admin = create_user(
            username="pagination_admin",
            email="pagination-admin@example.test",
            document="PAGINATION-ADMIN",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        self.product = make_product()
        self.series = make_series(
            admin=self.admin,
            product=self.product,
            target=1,
        )
        base_draw = timezone.now() + timedelta(days=2)
        for sequence in range(1, 32):
            DrawEvent.objects.create(
                series=self.series,
                series_sequence=sequence,
                product=self.product,
                name=f"Evento paginado {sequence}",
                sales_open_at=base_draw - timedelta(hours=1),
                draw_at=base_draw + timedelta(hours=sequence),
                price_minor=100,
                prize_minor=5000,
                status=DrawEvent.Status.DRAFT,
            )
        self.client.force_login(self.admin)
        session = self.client.session
        session[ACTIVE_MODE_SESSION_KEY] = ADMINISTRATOR
        session.save()

    def test_product_detail_paginates_events(self):
        response = self.client.get(reverse("lottery:product_detail", args=(self.product.pk,)))
        self.assertEqual(len(response.context["events_page"].object_list), 15)
        self.assertTrue(response.context["events_page"].has_next())

    def test_series_detail_paginates_generated_events(self):
        response = self.client.get(reverse("lottery:series_detail", args=(self.series.pk,)))
        self.assertEqual(
            len(response.context["generated_events_page"].object_list),
            30,
        )
        self.assertTrue(response.context["generated_events_page"].has_next())


class PurchaseAuthorizationRegressionTests(TestCase):
    def test_service_rejects_client_role_in_vendor_mode(self):
        user = create_user(
            username="multirole_purchase",
            email="multirole-purchase@example.test",
            document="MULTI-PURCHASE",
            roles=(CLIENT, VENDOR),
        )
        product = make_product()
        now = timezone.now()
        event = DrawEvent.objects.create(
            product=product,
            name="Evento compra por modo",
            sales_open_at=now - timedelta(minutes=5),
            draw_at=now + timedelta(hours=2),
            price_minor=100,
            prize_minor=5000,
            status=DrawEvent.Status.SALES_OPEN,
        )
        Wallet.objects.filter(
            user=user,
            currency=Wallet.Currency.VIRTUAL,
        ).update(available_minor=1000)

        with self.assertRaises(ValidationError):
            purchase_ticket(
                user=user,
                active_mode=VENDOR,
                event_id=event.pk,
                combination="0123",
                operation_id=uuid.uuid4(),
            )
        self.assertEqual(event.tickets.count(), 0)


class SharedSeriesValidationTests(TestCase):
    def test_model_and_form_reject_same_invalid_timing(self):
        admin = create_user(
            username="shared_series_validation",
            email="shared-series-validation@example.test",
            document="SHARED-SERIES",
            roles=(ADMINISTRATOR,),
            is_staff=True,
        )
        product = make_product()
        first_draw = timezone.now() + timedelta(days=1)
        series = DrawEventSeries(
            name_prefix="Serie inválida",
            product=product,
            first_draw_at=first_draw,
            next_draw_at=first_draw,
            recurrence_minutes=60,
            sales_lead_minutes=120,
            price_minor=100,
            prize_minor=5000,
            future_events_target=1,
            created_by=admin,
        )
        with self.assertRaises(ValidationError) as model_error:
            series.full_clean()
        self.assertIn("sales_lead_minutes", model_error.exception.message_dict)

        form = DrawEventSeriesForm(
            data={
                "name_prefix": "Serie inválida",
                "product": product.pk,
                "first_draw_at": first_draw.strftime("%Y-%m-%dT%H:%M"),
                "next_draw_at": first_draw.strftime("%Y-%m-%dT%H:%M"),
                "recurrence_minutes": 60,
                "sales_lead_minutes": 120,
                "price_minor": "1.00",
                "prize_minor": "50.00",
                "future_events_target": 1,
                "result_mode": DrawEventSeries.ResultMode.MANUAL,
                "occurrence_mode": DrawEventSeriesForm.OccurrenceMode.UNLIMITED,
                "is_active": "on",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("sales_lead_minutes", form.errors)
