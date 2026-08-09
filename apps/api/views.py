from __future__ import annotations

from django.http import Http404, HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.lottery.models import DrawEvent, DrawResult, LotteryProduct


def _money(amount_minor: int) -> dict[str, object]:
    return {
        "minor": int(amount_minor),
        "display": f"V {int(amount_minor) / 100:,.2f}",
    }


def _product_data(product: LotteryProduct) -> dict[str, object]:
    return {
        "id": product.pk,
        "code": product.code,
        "name": product.name,
        "kind": product.kind,
        "kind_label": product.get_kind_display(),
        "symbols": list(product.symbol_tokens),
        "selection_count": product.selection_count,
        "accent_color": product.accent_color,
        "is_active": product.is_active,
    }


def _event_data(event: DrawEvent) -> dict[str, object]:
    return {
        "id": event.pk,
        "name": event.name,
        "product": _product_data(event.product),
        "status": event.status,
        "status_label": event.get_status_display(),
        "sales_open_at": event.sales_open_at.isoformat(),
        "sales_close_at": event.sales_close_at.isoformat(),
        "draw_at": event.draw_at.isoformat(),
        "price": _money(event.price_minor),
        "prize": _money(event.prize_minor),
        "is_open_now": (
            event.status == DrawEvent.Status.SALES_OPEN
            and timezone.now() < event.sales_close_at
        ),
    }


def _result_data(result: DrawResult) -> dict[str, object]:
    return {
        "id": result.pk,
        "event": {
            "id": result.event_id,
            "name": result.event.name,
            "product": _product_data(result.event.product),
            "draw_at": result.event.draw_at.isoformat(),
        },
        "winning_key": result.winning_key,
        "winning_symbols": list(result.key_tokens),
        "publication_source": result.publication_source,
        "publication_source_label": result.get_publication_source_display(),
        "published_at": result.published_at.isoformat(),
    }


@require_GET
def api_root(request: HttpRequest) -> JsonResponse:
    return JsonResponse({
        "name": "Lotería Binaria API pública",
        "version": "1.0",
        "endpoints": {
            "products": request.build_absolute_uri("/api/products/"),
            "events": request.build_absolute_uri("/api/events/"),
            "results": request.build_absolute_uri("/api/results/"),
        },
    })


@require_GET
def product_list(request: HttpRequest) -> JsonResponse:
    queryset = LotteryProduct.objects.filter(is_active=True).order_by("id")
    query = request.GET.get("q", "").strip()
    kind = request.GET.get("kind", "").strip().upper()
    if query:
        queryset = queryset.filter(name__icontains=query)
    if kind in {choice for choice, _ in LotteryProduct.Kind.choices}:
        queryset = queryset.filter(kind=kind)
    data = [_product_data(product) for product in queryset]
    return JsonResponse({"count": len(data), "results": data})


@require_GET
def product_detail(request: HttpRequest, pk: int) -> JsonResponse:
    product = LotteryProduct.objects.filter(pk=pk, is_active=True).first()
    if product is None:
        raise Http404("Producto no encontrado.")
    return JsonResponse(_product_data(product))


def _public_events():
    return (
        DrawEvent.objects
        .filter(
            product__is_active=True,
            status__in=(
                DrawEvent.Status.SCHEDULED,
                DrawEvent.Status.PUBLISHED,
                DrawEvent.Status.SALES_OPEN,
                DrawEvent.Status.SALES_CLOSED,
                DrawEvent.Status.RESULT_SET,
                DrawEvent.Status.FINISHED,
                DrawEvent.Status.CANCELLED,
            ),
        )
        .select_related("product")
        .order_by("-draw_at", "-id")
    )


@require_GET
def event_list(request: HttpRequest) -> JsonResponse:
    queryset = _public_events()
    product_id = request.GET.get("product", "").strip()
    status = request.GET.get("status", "").strip().upper()
    query = request.GET.get("q", "").strip()
    if product_id.isdigit():
        queryset = queryset.filter(product_id=int(product_id))
    valid_statuses = {choice for choice, _ in DrawEvent.Status.choices}
    if status in valid_statuses:
        queryset = queryset.filter(status=status)
    if query:
        queryset = queryset.filter(name__icontains=query)
    data = [_event_data(event) for event in queryset[:100]]
    return JsonResponse({"count": len(data), "results": data})


@require_GET
def event_detail(request: HttpRequest, pk: int) -> JsonResponse:
    event = _public_events().filter(pk=pk).first()
    if event is None:
        raise Http404("Sorteo no encontrado.")
    return JsonResponse(_event_data(event))


@require_GET
def result_list(request: HttpRequest) -> JsonResponse:
    queryset = (
        DrawResult.objects
        .select_related("event", "event__product")
        .order_by("-published_at", "-id")
    )
    product_id = request.GET.get("product", "").strip()
    if product_id.isdigit():
        queryset = queryset.filter(event__product_id=int(product_id))
    data = [_result_data(result) for result in queryset[:100]]
    return JsonResponse({"count": len(data), "results": data})


@require_GET
def result_detail(request: HttpRequest, pk: int) -> JsonResponse:
    result = (
        DrawResult.objects
        .select_related("event", "event__product")
        .filter(pk=pk)
        .first()
    )
    if result is None:
        raise Http404("Resultado no encontrado.")
    return JsonResponse(_result_data(result))
