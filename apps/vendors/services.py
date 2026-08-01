"""Servicios transaccionales del módulo vendors."""

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.db.models.deletion import ProtectedError

from .models import VendorProfile


@dataclass(frozen=True)
class VendorProfileRemovalResult:
    """Resultado de eliminar físicamente o desactivar un perfil."""

    profile_id: int
    username: str
    physically_deleted: bool
    deactivated: bool


def vendor_profile_has_history(profile: VendorProfile) -> bool:
    """Devuelve True cuando el perfil conserva relaciones históricas.

    La inspección usa las relaciones declaradas por Django. Actualmente cubre
    asignaciones y, cuando se agreguen compras u otras relaciones protegidas
    hacia VendorProfile, también quedarán detectadas sin depender de SQL
    exclusivo de una base concreta.
    """
    for relation in profile._meta.related_objects:
        if relation.many_to_many:
            continue

        accessor_name = relation.get_accessor_name()

        if relation.one_to_one:
            try:
                getattr(profile, accessor_name)
            except relation.related_model.DoesNotExist:
                continue
            return True

        related_manager = getattr(profile, accessor_name, None)
        if related_manager is not None and related_manager.exists():
            return True

    return False


@transaction.atomic
def remove_or_deactivate_vendor_profile(
    *,
    profile_id: int,
) -> VendorProfileRemovalResult:
    """Elimina solo perfiles sin historia; en otro caso los desactiva."""
    profile = (
        VendorProfile.objects
        .select_for_update()
        .select_related("user")
        .get(pk=profile_id)
    )
    username = profile.user.username

    if vendor_profile_has_history(profile):
        if profile.status != VendorProfile.Status.DISABLED:
            profile.status = VendorProfile.Status.DISABLED
            profile.save(update_fields=("status", "updated_at"))

        return VendorProfileRemovalResult(
            profile_id=profile_id,
            username=username,
            physically_deleted=False,
            deactivated=True,
        )

    try:
        profile.delete()
    except ProtectedError:
        profile.status = VendorProfile.Status.DISABLED
        profile.save(update_fields=("status", "updated_at"))
        return VendorProfileRemovalResult(
            profile_id=profile_id,
            username=username,
            physically_deleted=False,
            deactivated=True,
        )

    return VendorProfileRemovalResult(
        profile_id=profile_id,
        username=username,
        physically_deleted=True,
        deactivated=False,
    )
