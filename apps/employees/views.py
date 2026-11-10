from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.access import FINANCE_ROLES, require_company, require_roles

from .forms import EmployeeForm
from .models import Employee


def _employee(request, pk):
    return get_object_or_404(Employee, pk=pk, company=request.company)


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*FINANCE_ROLES)
def employee_detail(request, pk):
    emp = _employee(request, pk)
    return render(
        request,
        "employees/employee_detail.html",
        {
            "employee": emp,
            "company": request.company,
            "trip_count": emp.trips_driven.aggregate(t=Coalesce(Sum("trip_count"), Value(0)))[
                "t"
            ],
            "fuel_count": emp.fuel_entries.count(),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def employee_edit(request, pk):
    emp = _employee(request, pk)
    if request.method == "POST":
        form = EmployeeForm(request.POST, company=request.company, instance=emp)
        if form.is_valid():
            form.save()
            messages.success(request, "Funcionário atualizado.")
            return redirect(reverse("employees:detail", kwargs={"pk": emp.pk}))
    else:
        form = EmployeeForm(company=request.company, instance=emp)
    return render(
        request,
        "employees/employee_form_edit.html",
        {"form": form, "employee": emp, "company": request.company},
    )


@login_required
@require_POST
@require_company
@require_roles(*FINANCE_ROLES)
def employee_delete(request, pk):
    emp = _employee(request, pk)
    name = emp.name
    if emp.trips_driven.exists() or emp.fuel_entries.exists():
        messages.error(
            request,
            "Não é possível excluir: existem viagens ou abastecimentos associados a este motorista.",
        )
        return redirect(reverse("employees:detail", kwargs={"pk": pk}))
    emp.delete()
    messages.success(request, f"Funcionário «{name}» removido.")
    return redirect(reverse("employees:list"))


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def employee_list(request):
    company = request.company
    if request.method == "POST":
        form = EmployeeForm(request.POST, company=company)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Funcionário guardado.")
            return redirect(reverse("employees:detail", kwargs={"pk": obj.pk}))
    else:
        form = EmployeeForm(company=company)

    employees = Employee.objects.filter(company=company).select_related("truck").order_by("name")
    return render(
        request,
        "employees/employee_list.html",
        {"form": form, "employees": employees, "company": company},
    )
