from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.models import MembershipRole
from apps.core.access import OPS_ROLES, require_company, require_roles
from apps.employees.models import Employee

from .forms import TripForm
from .models import Trip


def _trip_for_request(request, pk):
    trip = get_object_or_404(
        Trip.objects.filter(company=request.company).select_related(
            "truck", "driver", "customer", "delivery_place_ref", "payment_method", "financial_entry"
        ),
        pk=pk,
    )
    return trip


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*OPS_ROLES)
def trip_detail(request, pk):
    trip = _trip_for_request(request, pk)
    membership = request.membership
    if membership.role == MembershipRole.DRIVER:
        de = Employee.objects.filter(user=request.user, company=request.company).first()
        if de is None or trip.driver_id != de.pk:
            return redirect(reverse("finance:receitas"))
    return render(
        request,
        "trips/trip_detail.html",
        {
            "trip": trip,
            "company": request.company,
            "is_driver": membership.role == MembershipRole.DRIVER,
            "show_finance_subnav": membership.role != MembershipRole.DRIVER,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*OPS_ROLES)
def trip_edit(request, pk):
    trip = _trip_for_request(request, pk)
    company = request.company
    membership = request.membership

    driver_employee = None
    if membership.role == MembershipRole.DRIVER:
        driver_employee = Employee.objects.filter(user=request.user, company=company).first()
        if driver_employee is None or trip.driver_id != driver_employee.pk:
            messages.error(
                request,
                "Só pode editar as suas próprias viagens.",
            )
            return redirect(reverse("finance:receitas"))

    if request.method == "POST":
        form = TripForm(
            request.POST,
            company=company,
            user=request.user,
            driver_employee=driver_employee,
            instance=trip,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Receita atualizada no financeiro.")
            return redirect(reverse("finance:receitas_detail", kwargs={"pk": trip.pk}))
    else:
        form = TripForm(
            company=company,
            user=request.user,
            driver_employee=driver_employee,
            instance=trip,
        )

    return render(
        request,
        "trips/trip_form_edit.html",
        {
            "form": form,
            "trip": trip,
            "company": company,
            "is_driver": membership.role == MembershipRole.DRIVER,
            "show_finance_subnav": membership.role != MembershipRole.DRIVER,
        },
    )


@login_required
@require_POST
@require_company
@require_roles(*OPS_ROLES)
def trip_delete(request, pk):
    trip = _trip_for_request(request, pk)
    membership = request.membership
    if membership.role == MembershipRole.DRIVER:
        driver_employee = Employee.objects.filter(user=request.user, company=request.company).first()
        if driver_employee is None or trip.driver_id != driver_employee.pk:
            messages.error(request, "Não tem permissão para excluir esta viagem.")
            return redirect(reverse("finance:receitas"))

    desc = f"{trip.trip_date} — {trip.customer.name}"
    trip.delete()
    messages.success(request, f"Viagem removida ({desc}).")
    return redirect(reverse("finance:receitas"))


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*OPS_ROLES)
def trip_list(request):
    company = request.company
    membership = request.membership

    driver_employee = None
    if membership.role == MembershipRole.DRIVER:
        driver_employee = Employee.objects.filter(user=request.user, company=company).first()
        if driver_employee is None:
            messages.warning(
                request,
                "A sua conta de motorista ainda não está ligada a um funcionário. "
                "Peça ao administrador para associar o seu utilizador ao registo de funcionário.",
            )
            return redirect(reverse("dashboard:home"))

    if request.method == "POST":
        form = TripForm(
            request.POST,
            company=company,
            user=request.user,
            driver_employee=driver_employee,
        )
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Receita registada (lançamento criado no financeiro).")
            return redirect(reverse("finance:receitas_detail", kwargs={"pk": obj.pk}))
    else:
        form = TripForm(company=company, user=request.user, driver_employee=driver_employee)

    trips_qs = Trip.objects.filter(company=company).select_related(
        "truck", "driver", "customer", "delivery_place_ref"
    )
    if membership.role == MembershipRole.DRIVER and driver_employee:
        trips_qs = trips_qs.filter(driver=driver_employee)
    trips_qs = trips_qs.order_by("-trip_date", "-pk")[:200]

    return render(
        request,
        "trips/trip_list.html",
        {
            "form": form,
            "trips": trips_qs,
            "company": company,
            "is_driver": membership.role == MembershipRole.DRIVER,
            "show_finance_subnav": membership.role != MembershipRole.DRIVER,
        },
    )
