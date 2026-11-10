from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.access import FINANCE_ROLES, require_company, require_roles

from .forms import TruckForm
from .models import Truck


def _truck(request, pk):
    return get_object_or_404(Truck, pk=pk, company=request.company)


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*FINANCE_ROLES)
def truck_detail(request, pk):
    truck = _truck(request, pk)
    trip_n = truck.trips.aggregate(t=Coalesce(Sum("trip_count"), Value(0)))["t"]
    return render(
        request,
        "trucks/truck_detail.html",
        {
            "truck": truck,
            "company": request.company,
            "trip_count": trip_n,
            "has_operational_links": trip_n > 0
            or truck.fuel_entries.exists()
            or truck.maintenance_records.exists()
            or truck.assigned_employees.exists(),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def truck_edit(request, pk):
    truck = _truck(request, pk)
    if request.method == "POST":
        form = TruckForm(request.POST, company=request.company, instance=truck)
        if form.is_valid():
            form.save()
            messages.success(request, "Caminhão atualizado.")
            return redirect(reverse("trucks:detail", kwargs={"pk": truck.pk}))
    else:
        form = TruckForm(company=request.company, instance=truck)
    return render(
        request,
        "trucks/truck_form_edit.html",
        {"form": form, "truck": truck, "company": request.company},
    )


@login_required
@require_POST
@require_company
@require_roles(*FINANCE_ROLES)
def truck_delete(request, pk):
    truck = _truck(request, pk)
    plate = truck.plate
    if (
        truck.trips.exists()
        or truck.fuel_entries.exists()
        or truck.maintenance_records.exists()
        or truck.assigned_employees.exists()
    ):
        messages.error(
            request,
            "Não é possível excluir: este caminhão está referenciado em viagens, abastecimentos, "
            "manutenção ou funcionários. Altere ou remova esses registos primeiro.",
        )
        return redirect(reverse("trucks:detail", kwargs={"pk": pk}))
    truck.delete()
    messages.success(request, f"Caminhão «{plate}» removido.")
    return redirect(reverse("trucks:list"))


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def truck_list(request):
    company = request.company
    if request.method == "POST":
        form = TruckForm(request.POST, company=company)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Caminhão guardado.")
            return redirect(reverse("trucks:detail", kwargs={"pk": obj.pk}))
    else:
        form = TruckForm(company=company)

    trucks = Truck.objects.filter(company=company).order_by("plate")
    return render(
        request,
        "trucks/truck_list.html",
        {"form": form, "trucks": trucks, "company": company},
    )
