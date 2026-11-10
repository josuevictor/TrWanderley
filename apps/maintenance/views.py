from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.access import FINANCE_ROLES, require_company, require_roles

from .forms import MaintenanceForm
from .models import MaintenanceRecord


def _maintenance(request, pk):
    return get_object_or_404(
        MaintenanceRecord.objects.filter(company=request.company).select_related(
            "truck", "workshop"
        ),
        pk=pk,
    )


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*FINANCE_ROLES)
def maintenance_detail(request, pk):
    rec = _maintenance(request, pk)
    return render(
        request,
        "maintenance/maintenance_detail.html",
        {"record": rec, "company": request.company},
    )


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def maintenance_edit(request, pk):
    rec = _maintenance(request, pk)
    if request.method == "POST":
        form = MaintenanceForm(request.POST, request.FILES, company=request.company, instance=rec)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except Exception as exc:
                messages.error(
                    request,
                    "Não foi possível guardar. Verifique os valores e tente novamente. "
                    f"Detalhe: {exc}",
                )
            else:
                messages.success(request, "Manutenção atualizada.")
                return redirect(reverse("maintenance:detail", kwargs={"pk": rec.pk}))
    else:
        form = MaintenanceForm(company=request.company, instance=rec)
    return render(
        request,
        "maintenance/maintenance_form_edit.html",
        {"form": form, "record": rec, "company": request.company},
    )


@login_required
@require_POST
@require_company
@require_roles(*FINANCE_ROLES)
def maintenance_delete(request, pk):
    rec = _maintenance(request, pk)
    title = rec.title or str(rec.service_date)
    rec.delete()
    messages.success(request, f"Registo de manutenção removido ({title}).")
    return redirect(reverse("maintenance:list"))


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def maintenance_list(request):
    company = request.company
    if request.method == "POST":
        form = MaintenanceForm(request.POST, request.FILES, company=company)
        if form.is_valid():
            try:
                with transaction.atomic():
                    obj = form.save()
            except Exception as exc:
                messages.error(
                    request,
                    "Não foi possível guardar. Verifique os valores e tente novamente. "
                    f"Detalhe: {exc}",
                )
            else:
                messages.success(request, "Manutenção registada com sucesso.")
                return redirect(reverse("maintenance:detail", kwargs={"pk": obj.pk}))
    else:
        form = MaintenanceForm(company=company)

    records = (
        MaintenanceRecord.objects.filter(company=company)
        .select_related("truck")
        .order_by("-service_date", "-pk")[:200]
    )
    return render(
        request,
        "maintenance/maintenance_list.html",
        {"form": form, "records": records, "company": company},
    )
