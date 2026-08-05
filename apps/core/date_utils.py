"""Utilidades de fechas locales portables entre SQLite y MySQL."""

from datetime import date, datetime, time, timedelta

from django.utils import timezone


def local_date_bounds(value: date):
    """Devuelve [inicio, fin) del día en la zona horaria activa."""

    current_tz = timezone.get_current_timezone()
    start = timezone.make_aware(
        datetime.combine(value, time.min),
        current_tz,
    )
    end = timezone.make_aware(
        datetime.combine(value + timedelta(days=1), time.min),
        current_tz,
    )
    return start, end
