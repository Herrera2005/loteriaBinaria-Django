from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth.models import Group
from django.utils import timezone

from apps.accounts.models import TermsVersion, User


VALID_PASSWORD = "T3cn0l0g1@"


def adult_birth_date(years: int = 25) -> date:
    today = timezone.localdate()
    try:
        return today.replace(year=today.year - years)
    except ValueError:
        return today.replace(year=today.year - years, month=2, day=28)


def create_terms_versions() -> tuple[TermsVersion, TermsVersion]:
    effective_at = timezone.now() - timedelta(days=1)
    terms, _ = TermsVersion.objects.get_or_create(
        kind=TermsVersion.Kind.TERMS,
        version="test-1",
        defaults={
            "title": "Términos de prueba",
            "content": "Contenido académico de prueba.",
            "effective_at": effective_at,
            "is_active": True,
        },
    )
    privacy, _ = TermsVersion.objects.get_or_create(
        kind=TermsVersion.Kind.PRIVACY,
        version="test-1",
        defaults={
            "title": "Privacidad de prueba",
            "content": "Contenido académico de privacidad.",
            "effective_at": effective_at,
            "is_active": True,
        },
    )
    return terms, privacy


def create_user(
    *,
    username: str = "usuario_prueba",
    email: str = "usuario@example.test",
    document: str = "TEST-001",
    status: str = User.Status.ACTIVE,
    roles: tuple[str, ...] = (),
    is_staff: bool = False,
    is_superuser: bool = False,
) -> User:
    user = User.objects.create_user(
        username=username,
        email=email,
        document=document,
        phone="",
        birth_date=adult_birth_date(),
        password=VALID_PASSWORD,
        status=status,
        is_active=status == User.Status.ACTIVE,
        is_staff=is_staff,
        is_superuser=is_superuser,
    )
    for role in roles:
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
    return user
