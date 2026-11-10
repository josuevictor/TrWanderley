from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.access import FINANCE_ROLES, require_company, require_roles
from apps.trips.models import Trip

from .forms import CustomerForm, delivery_places_formset_factory
from .models import Customer


def _customer_for_company(request, pk):
    return get_object_or_404(Customer, pk=pk, company=request.company)


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def customer_list(request):
    company = request.company
    if request.method == "POST":
        form = CustomerForm(request.POST, company=company)
        places_fs = delivery_places_formset_factory(customer=None, data=request.POST)
        form_ok = form.is_valid()
        fs_ok = places_fs.is_valid()
        if form_ok and fs_ok:
            has_place = False
            for f in places_fs.forms:
                cd = getattr(f, "cleaned_data", None)
                if not cd or cd.get("DELETE"):
                    continue
                if (cd.get("address_line") or "").strip():
                    has_place = True
                    break
            if not has_place:
                messages.error(request, "Indique pelo menos um local de entrega (endereço ou referência).")
            else:
                obj = form.save()
                places_fs.instance = obj
                places_fs.save()
                messages.success(request, "Cliente e locais de entrega guardados.")
                return redirect(reverse("customers:detail", kwargs={"pk": obj.pk}))
    else:
        form = CustomerForm(company=company)
        places_fs = delivery_places_formset_factory(customer=None)

    rows = Customer.objects.filter(company=company).order_by("name")
    return render(
        request,
        "customers/customer_list.html",
        {"form": form, "places_fs": places_fs, "customers": rows, "company": company},
    )


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*FINANCE_ROLES)
def customer_detail(request, pk):
    customer = get_object_or_404(
        Customer.objects.prefetch_related("delivery_places"),
        pk=pk,
        company=request.company,
    )
    trip_count = Trip.objects.filter(company=request.company, customer=customer).aggregate(
        t=Coalesce(Sum("trip_count"), Value(0))
    )["t"]
    delivery_places = list(customer.delivery_places.all())
    return render(
        request,
        "customers/customer_detail.html",
        {
            "customer": customer,
            "delivery_places": delivery_places,
            "trip_count": trip_count,
            "company": request.company,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def customer_edit(request, pk):
    customer = _customer_for_company(request, pk)
    if request.method == "POST":
        form = CustomerForm(request.POST, company=request.company, instance=customer)
        places_fs = delivery_places_formset_factory(customer=customer, data=request.POST)
        if form.is_valid() and places_fs.is_valid():
            form.save()
            places_fs.instance = customer
            places_fs.save()
            messages.success(request, "Cliente e locais de entrega atualizados.")
            return redirect(reverse("customers:detail", kwargs={"pk": customer.pk}))
    else:
        form = CustomerForm(company=request.company, instance=customer)
        places_fs = delivery_places_formset_factory(customer=customer)
    return render(
        request,
        "customers/customer_form_edit.html",
        {"form": form, "places_fs": places_fs, "customer": customer, "company": request.company},
    )


@login_required
@require_POST
@require_company
@require_roles(*FINANCE_ROLES)
def customer_delete(request, pk):
    customer = _customer_for_company(request, pk)
    if Trip.objects.filter(company=request.company, customer=customer).exists():
        messages.error(
            request,
            "Não é possível excluir: existem viagens associadas a este cliente. "
            "Altere ou remova as viagens primeiro.",
        )
        return redirect(reverse("customers:detail", kwargs={"pk": pk}))

    name = customer.name
    customer.delete()
    messages.success(request, f"Cliente «{name}» removido.")
    return redirect(reverse("customers:list"))
