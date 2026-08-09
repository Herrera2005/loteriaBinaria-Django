from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import User
from apps.accounts.roles import ROLE_CODES


@receiver(post_save, sender=User)
def assign_all_roles_to_superuser(sender, instance, **kwargs):
    """
    Todo superusuario debe disponer de los tres modos del Taller #3.

    Los grupos se crean si todavía no existen para que createsuperuser
    funcione incluso antes de ejecutar seed_baseline.
    """
    if not instance.is_superuser:
        return

    groups = [
        Group.objects.get_or_create(name=role_code)[0]
        for role_code in ROLE_CODES
    ]

    instance.groups.add(*groups)