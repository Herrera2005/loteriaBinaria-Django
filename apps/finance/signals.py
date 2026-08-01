"""Integración controlada entre roles de Accounts y wallets de Finance."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from apps.accounts.roles import ROLE_CODES

from .services import ensure_user_wallets


User = get_user_model()


@receiver(
    m2m_changed,
    sender=User.groups.through,
    dispatch_uid="finance.ensure_wallets_on_role_assignment",
)
def ensure_wallets_on_role_assignment(
    sender,
    instance,
    action,
    reverse,
    model,
    pk_set,
    **kwargs,
) -> None:
    """Provisiona wallets al asignar el primer rol operativo al usuario."""

    if reverse or action != "post_add" or not pk_set:
        return

    if instance.groups.filter(name__in=ROLE_CODES).exists():
        ensure_user_wallets(instance)
