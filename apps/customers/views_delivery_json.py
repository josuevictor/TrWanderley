"""JSON auxiliar para formulários (viagens)."""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from apps.core.access import OPS_ROLES, require_company, require_roles

from .models import Customer


@login_required
@require_GET
@require_company
@require_roles(*OPS_ROLES)
def customer_delivery_places_json(request, pk):
    customer = get_object_or_404(Customer, pk=pk, company=request.company)
    places = []
    for p in customer.delivery_places.all():
        label = (p.label or "").strip()
        if label:
            opt_label = f"{label} — {p.address_line}"
        else:
            opt_label = p.address_line
        places.append(
            {
                "id": p.pk,
                "label": opt_label,
                "address_line": p.address_line,
            }
        )
    return JsonResponse(
        {
            "customer_id": customer.pk,
            "places": places,
        },
        json_dumps_params={"ensure_ascii": False},
    )
