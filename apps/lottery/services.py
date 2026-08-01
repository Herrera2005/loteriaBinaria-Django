"""Servicios transaccionales del CRUD administrativo de lottery."""
from dataclasses import dataclass
from django.db import transaction
from django.db.models.deletion import ProtectedError
from .models import DrawEvent, DrawResult, LotteryProduct

@dataclass(frozen=True)
class DeleteResult:
    object_id: int
    label: str
    deleted: bool
    reason: str = ""

@transaction.atomic
def delete_lottery_product(*, product_id: int) -> DeleteResult:
    product = LotteryProduct.objects.select_for_update().get(pk=product_id)
    if product.events.exists():
        return DeleteResult(product.pk, product.name, False, "El producto tiene eventos relacionados y no puede eliminarse.")
    try:
        product.delete()
    except ProtectedError:
        return DeleteResult(product.pk, product.name, False, "El producto conserva relaciones protegidas y no puede eliminarse.")
    return DeleteResult(product_id, product.name, True)

@transaction.atomic
def delete_draw_event(*, event_id: int) -> DeleteResult:
    event = DrawEvent.objects.select_for_update().get(pk=event_id)
    if event.status != DrawEvent.Status.DRAFT:
        return DeleteResult(event.pk, event.name, False, "Solo se puede eliminar un evento en estado Borrador.")
    if event.tickets.exists():
        return DeleteResult(event.pk, event.name, False, "El evento tiene boletos históricos y no puede eliminarse.")
    try:
        event.result
    except DrawResult.DoesNotExist:
        pass
    else:
        return DeleteResult(event.pk, event.name, False, "El evento tiene un resultado histórico y no puede eliminarse.")
    try:
        event.delete()
    except ProtectedError:
        return DeleteResult(event.pk, event.name, False, "El evento conserva relaciones protegidas y no puede eliminarse.")
    return DeleteResult(event_id, event.name, True)

def event_can_be_deleted(event: DrawEvent) -> bool:
    if event.status != DrawEvent.Status.DRAFT or event.tickets.exists():
        return False
    try:
        event.result
    except DrawResult.DoesNotExist:
        return True
    return False
