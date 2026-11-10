from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.access import FINANCE_ROLES, require_company, require_roles

from .forms import SupplierForm
from .models import Supplier


def _supplier(request, pk):
    return get_object_or_404(Supplier, pk=pk, company=request.company)


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*FINANCE_ROLES)
def supplier_detail(request, pk):
    sup = _supplier(request, pk)
    return render(
        request,
        "suppliers/supplier_detail.html",
        {
            "supplier": sup,
            "company": request.company,
            "fuel_n": sup.fuel_entries.count(),
            "maint_n": sup.maintenance_jobs.count(),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def supplier_edit(request, pk):
    sup = _supplier(request, pk)
    if request.method == "POST":
        form = SupplierForm(request.POST, company=request.company, instance=sup)
        if form.is_valid():
            form.save()
            messages.success(request, "Fornecedor atualizado.")
            return redirect(reverse("suppliers:detail", kwargs={"pk": sup.pk}))
    else:
        form = SupplierForm(company=request.company, instance=sup)
    return render(
        request,
        "suppliers/supplier_form_edit.html",
        {"form": form, "supplier": sup, "company": request.company},
    )


@login_required
@require_POST
@require_company
@require_roles(*FINANCE_ROLES)
def supplier_delete(request, pk):
    sup = _supplier(request, pk)
    name = sup.name
    if sup.fuel_entries.exists() or sup.maintenance_jobs.exists():
        messages.error(
            request,
            "Não é possível excluir: o fornecedor está em abastecimentos ou manutenção.",
        )
        return redirect(reverse("suppliers:detail", kwargs={"pk": pk}))
    sup.delete()
    messages.success(request, f"Fornecedor «{name}» removido.")
    return redirect(reverse("suppliers:list"))


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def supplier_list(request):
    company = request.company
    if request.method == "POST":
        form = SupplierForm(request.POST, company=company)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Fornecedor guardado.")
            return redirect(reverse("suppliers:detail", kwargs={"pk": obj.pk}))
    else:
        form = SupplierForm(company=company)

    rows = Supplier.objects.filter(company=company).order_by("name")
    return render(
        request,
        "suppliers/supplier_list.html",
        {"form": form, "suppliers": rows, "company": company},
    )
