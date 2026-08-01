"""Datos mínimos idempotentes; no carga JSON legado."""

from datetime import timedelta

from django.contrib.auth.models import Group
from django.utils import timezone

from apps.accounts.models import TermsVersion
from apps.accounts.roles import ROLE_CODES


def ensure_role_groups() -> dict[str, Group]:
    groups = {}
    for name in ROLE_CODES:
        group, _ = Group.objects.get_or_create(name=name)
        groups[name] = group
    return groups


def ensure_legal_versions() -> dict[str, TermsVersion]:
    effective_at = timezone.now() - timedelta(days=30)
    terms, _ = TermsVersion.objects.get_or_create(
        kind=TermsVersion.Kind.TERMS,
        version="1.1.0",
        defaults={
            "title": "Términos académicos del Taller #3",
            "content": (
                "Condiciones de uso de la simulación académica Lotería Binaria."
            ),
            "effective_at": effective_at,
            "is_active": True,
        },
    )
    privacy, _ = TermsVersion.objects.get_or_create(
        kind=TermsVersion.Kind.PRIVACY,
        version="1.1.0",
        defaults={
            "title": "Política académica de privacidad",
            "content": (
                "Tratamiento académico y mínimo de datos para el Taller #3."
            ),
            "effective_at": effective_at,
            "is_active": True,
        },
    )
    return {"terms": terms, "privacy": privacy}
