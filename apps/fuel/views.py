from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.models import MembershipRole
from apps.core.access import OPS_ROLES, require_company, require_roles
from apps.employees.models import Employee

from .forms import FuelEntryForm
from .models import FuelEntry


def _fuel(request, pk):
    return get_object_or_404(
        FuelEntry.objects.filter(company=request.company).select_related(
            "truck", "driver", "supplier", "payment_method"
        ),
        pk=pk,
    )


def _driver_employee(request):
    return Employee.objects.filter(user=request.user, company=request.company).first()


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*OPS_ROLES)
def fuel_detail(request, pk):
    entry = _fuel(request, pk)
    if request.membership.role == MembershipRole.DRIVER:
        de = _driver_employee(request)
        if de is None or entry.driver_id != de.pk:
            return redirect(reverse("fuel:list"))
    return render(
        request,
        "fuel/fuel_detail.html",
        {
            "entry": entry,
            "company": request.company,
            "is_driver": request.membership.role == MembershipRole.DRIVER,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*OPS_ROLES)
def fuel_edit(request, pk):
    company = request.company
    entry = _fuel(request, pk)
    driver_employee = None
    if request.membership.role == MembershipRole.DRIVER:
        driver_employee = _driver_employee(request)
        if driver_employee is None or entry.driver_id != driver_employee.pk:
            messages.error(request, "Só pode editar os seus próprios abastecimentos.")
            return redirect(reverse("fuel:list"))
    if request.method == "POST":
        form = FuelEntryForm(
            request.POST,
            request.FILES,
            company=company,
            driver_employee=driver_employee,
            instance=entry,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Abastecimento atualizado.")
            return redirect(reverse("fuel:detail", kwargs={"pk": entry.pk}))
    else:
        form = FuelEntryForm(company=company, driver_employee=driver_employee, instance=entry)
    return render(
        request,
        "fuel/fuel_form_edit.html",
        {
            "form": form,
            "entry": entry,
            "company": company,
            "is_driver": request.membership.role == MembershipRole.DRIVER,
        },
    )


@login_required
@require_POST
@require_company
@require_roles(*OPS_ROLES)
def fuel_delete(request, pk):
    entry = _fuel(request, pk)
    if request.membership.role == MembershipRole.DRIVER:
        de = _driver_employee(request)
        if de is None or entry.driver_id != de.pk:
            messages.error(request, "Não tem permissão para excluir este abastecimento.")
            return redirect(reverse("fuel:list"))
    plate = entry.truck.plate
    dt = entry.fuel_date
    entry.delete()
    messages.success(request, f"Abastecimento removido ({plate}, {dt}).")
    return redirect(reverse("fuel:list"))


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*OPS_ROLES)
def fuel_list(request):
    company = request.company
    membership = request.membership

    driver_employee = None
    if membership.role == MembershipRole.DRIVER:
        driver_employee = Employee.objects.filter(user=request.user, company=company).first()
        if driver_employee is None:
            messages.warning(
                request,
                "Associe o seu utilizador a um funcionário para registar abastecimentos.",
            )
            return redirect(reverse("dashboard:home"))

    if request.method == "POST":
        form = FuelEntryForm(
            request.POST,
            request.FILES,
            company=company,
            driver_employee=driver_employee,
        )
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Abastecimento registado.")
            return redirect(reverse("fuel:detail", kwargs={"pk": obj.pk}))
    else:
        form = FuelEntryForm(company=company, driver_employee=driver_employee)

    qs = FuelEntry.objects.filter(company=company).select_related("truck", "driver")
    if membership.role == MembershipRole.DRIVER and driver_employee:
        qs = qs.filter(driver=driver_employee)
    qs = qs.order_by("-fuel_date", "-pk")[:200]

    return render(
        request,
        "fuel/fuel_list.html",
        {
            "form": form,
            "entries": qs,
            "company": company,
            "is_driver": membership.role == MembershipRole.DRIVER,
        },
    )
