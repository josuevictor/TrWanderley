"""Views do módulo financeiro — listagens, criação e CRUD."""

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.access import FINANCE_ROLES, require_company, require_roles
from apps.finance.forms import (
    CashMovementForm,
    FinancialAccountForm,
    FinancialCategoryForm,
    FinancialEntryForm,
    PaymentMethodForm,
)
from apps.finance.models import (
    CashMovement,
    CashMovementKind,
    FinancialAccount,
    FinancialCategory,
    FinancialEntry,
    PaymentMethod,
)
from apps.finance.constants import PROTECTED_CATEGORY_SLUGS
from apps.finance.services import ensure_default_categories


def _category(request, pk):
    return get_object_or_404(FinancialCategory, pk=pk, company=request.company)


def _payment_method(request, pk):
    return get_object_or_404(PaymentMethod, pk=pk, company=request.company)


def _account(request, pk):
    return get_object_or_404(FinancialAccount, pk=pk, company=request.company)


def _entry(request, pk):
    return get_object_or_404(
        FinancialEntry.objects.filter(company=request.company).select_related("category"),
        pk=pk,
    )


def _cash_movement(request, pk):
    return get_object_or_404(
        CashMovement.objects.filter(company=request.company).select_related(
            "financial_account", "payment_method"
        ),
        pk=pk,
    )


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def finance_home(request):
    company = request.company
    ensure_default_categories(company)
    return render(
        request,
        "finance/home.html",
        {"company": company},
    )


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*FINANCE_ROLES)
def expenses_hub(request):
    company = request.company
    ensure_default_categories(company)
    return render(
        request,
        "finance/expenses.html",
        {"company": company},
    )


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*FINANCE_ROLES)
def finance_settings(request):
    company = request.company
    ensure_default_categories(company)
    return render(
        request,
        "finance/settings.html",
        {"company": company},
    )


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*FINANCE_ROLES)
def category_detail(request, pk):
    cat = _category(request, pk)
    return render(
        request,
        "finance/category_detail.html",
        {
            "category": cat,
            "company": request.company,
            "is_protected_category": bool(cat.slug and cat.slug in PROTECTED_CATEGORY_SLUGS),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def category_edit(request, pk):
    cat = _category(request, pk)
    if request.method == "POST":
        form = FinancialCategoryForm(request.POST, company=request.company, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria atualizada.")
            return redirect(reverse("finance:category_detail", kwargs={"pk": cat.pk}))
    else:
        form = FinancialCategoryForm(company=request.company, instance=cat)
    return render(
        request,
        "finance/category_form_edit.html",
        {"form": form, "category": cat, "company": request.company},
    )


@login_required
@require_POST
@require_company
@require_roles(*FINANCE_ROLES)
def category_delete(request, pk):
    cat = _category(request, pk)
    if cat.slug and cat.slug in PROTECTED_CATEGORY_SLUGS:
        messages.error(
            request,
            "Não é possível excluir categorias predefinidas do sistema (receitas/despesas operacionais).",
        )
        return redirect(reverse("finance:category_detail", kwargs={"pk": pk}))
    if cat.entries.exists():
        messages.error(
            request,
            "Não é possível excluir: existem lançamentos nesta categoria.",
        )
        return redirect(reverse("finance:category_detail", kwargs={"pk": pk}))
    name = cat.name
    cat.delete()
    messages.success(request, f"Categoria «{name}» removida.")
    return redirect(reverse("finance:categories"))


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def category_list(request):
    company = request.company
    ensure_default_categories(company)

    if request.method == "POST":
        form = FinancialCategoryForm(request.POST, company=company)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Categoria guardada.")
            return redirect(reverse("finance:category_detail", kwargs={"pk": obj.pk}))
    else:
        form = FinancialCategoryForm(company=company)

    categories = FinancialCategory.objects.filter(company=company).order_by("kind", "name")
    return render(
        request,
        "finance/category_list.html",
        {"form": form, "categories": categories, "company": company},
    )


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*FINANCE_ROLES)
def payment_method_detail(request, pk):
    pm = _payment_method(request, pk)
    return render(
        request,
        "finance/payment_method_detail.html",
        {"payment_method": pm, "company": request.company},
    )


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def payment_method_edit(request, pk):
    pm = _payment_method(request, pk)
    if request.method == "POST":
        form = PaymentMethodForm(request.POST, company=request.company, instance=pm)
        if form.is_valid():
            form.save()
            messages.success(request, "Forma de pagamento atualizada.")
            return redirect(reverse("finance:payment_method_detail", kwargs={"pk": pm.pk}))
    else:
        form = PaymentMethodForm(company=request.company, instance=pm)
    return render(
        request,
        "finance/payment_method_form_edit.html",
        {"form": form, "payment_method": pm, "company": request.company},
    )


@login_required
@require_POST
@require_company
@require_roles(*FINANCE_ROLES)
def payment_method_delete(request, pk):
    pm = _payment_method(request, pk)
    if (
        pm.trips.exists()
        or pm.fuel_entries.exists()
        or pm.entries.exists()
        or pm.cash_movements.exists()
    ):
        messages.error(
            request,
            "Não é possível excluir: a forma de pagamento está em uso (viagens, combustível, lançamentos ou caixa).",
        )
        return redirect(reverse("finance:payment_method_detail", kwargs={"pk": pk}))
    name = pm.name
    pm.delete()
    messages.success(request, f"Forma de pagamento «{name}» removida.")
    return redirect(reverse("finance:payment_methods"))


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def payment_method_list(request):
    company = request.company
    ensure_default_categories(company)

    if request.method == "POST":
        form = PaymentMethodForm(request.POST, company=company)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Forma de pagamento guardada.")
            return redirect(reverse("finance:payment_method_detail", kwargs={"pk": obj.pk}))
    else:
        form = PaymentMethodForm(company=company)

    payment_methods = PaymentMethod.objects.filter(company=company).order_by("name")
    return render(
        request,
        "finance/payment_method_list.html",
        {"form": form, "payment_methods": payment_methods, "company": company},
    )


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*FINANCE_ROLES)
def account_detail(request, pk):
    acc = _account(request, pk)
    return render(
        request,
        "finance/account_detail.html",
        {"account": acc, "company": request.company},
    )


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def account_edit(request, pk):
    acc = _account(request, pk)
    if request.method == "POST":
        form = FinancialAccountForm(request.POST, company=request.company, instance=acc)
        if form.is_valid():
            form.save()
            messages.success(request, "Conta atualizada.")
            return redirect(reverse("finance:account_detail", kwargs={"pk": acc.pk}))
    else:
        form = FinancialAccountForm(company=request.company, instance=acc)
    return render(
        request,
        "finance/account_form_edit.html",
        {"form": form, "account": acc, "company": request.company},
    )


@login_required
@require_POST
@require_company
@require_roles(*FINANCE_ROLES)
def account_delete(request, pk):
    acc = _account(request, pk)
    if acc.movements.exists():
        messages.error(
            request,
            "Não é possível excluir: existem movimentos de caixa nesta conta.",
        )
        return redirect(reverse("finance:account_detail", kwargs={"pk": pk}))
    name = acc.name
    acc.delete()
    messages.success(request, f"Conta «{name}» removida.")
    return redirect(reverse("finance:accounts"))


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def account_list(request):
    company = request.company
    ensure_default_categories(company)

    if request.method == "POST":
        form = FinancialAccountForm(request.POST, company=company)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Conta guardada.")
            return redirect(reverse("finance:account_detail", kwargs={"pk": obj.pk}))
    else:
        form = FinancialAccountForm(company=company)

    accounts = FinancialAccount.objects.filter(company=company).order_by("name")
    return render(
        request,
        "finance/account_list.html",
        {"form": form, "accounts": accounts, "company": company},
    )


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*FINANCE_ROLES)
def entry_detail(request, pk):
    entry = _entry(request, pk)
    return render(
        request,
        "finance/entry_detail.html",
        {"entry": entry, "company": request.company},
    )


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def entry_edit(request, pk):
    entry = _entry(request, pk)
    if entry.is_system_generated:
        messages.error(
            request,
            "Este lançamento é gerado pela operação (viagem, combustível ou manutenção). "
            "Edite o registo na área correspondente.",
        )
        return redirect(reverse("finance:entry_detail", kwargs={"pk": entry.pk}))
    if request.method == "POST":
        form = FinancialEntryForm(
            request.POST, company=request.company, user=request.user, instance=entry
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Lançamento atualizado.")
            return redirect(reverse("finance:entry_detail", kwargs={"pk": entry.pk}))
    else:
        form = FinancialEntryForm(company=request.company, user=request.user, instance=entry)
    return render(
        request,
        "finance/entry_form_edit.html",
        {"form": form, "entry": entry, "company": request.company},
    )


@login_required
@require_POST
@require_company
@require_roles(*FINANCE_ROLES)
def entry_delete(request, pk):
    entry = _entry(request, pk)
    if entry.is_system_generated:
        messages.error(
            request,
            "Não é possível excluir lançamentos gerados pela operação; remova ou altere a origem (viagem, combustível, manutenção).",
        )
        return redirect(reverse("finance:entry_detail", kwargs={"pk": pk}))
    if entry.payment_allocations.exists():
        messages.error(
            request,
            "Não é possível excluir: existem quitações de caixa ligadas a este lançamento.",
        )
        return redirect(reverse("finance:entry_detail", kwargs={"pk": pk}))
    desc = entry.description[:80]
    entry.delete()
    messages.success(request, f"Lançamento removido ({desc}).")
    return redirect(reverse("finance:entries"))


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def entry_list(request):
    company = request.company
    ensure_default_categories(company)

    if request.method == "POST":
        form = FinancialEntryForm(request.POST, company=company, user=request.user)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Lançamento guardado.")
            return redirect(reverse("finance:entry_detail", kwargs={"pk": obj.pk}))
    else:
        form = FinancialEntryForm(company=company, user=request.user)

    entries = (
        FinancialEntry.objects.filter(company=company, is_cancelled=False)
        .select_related("category")
        .order_by("-competence_date", "-pk")[:200]
    )
    return render(
        request,
        "finance/entry_list.html",
        {"form": form, "entries": entries, "company": company},
    )


@login_required
@require_http_methods(["GET"])
@require_company
@require_roles(*FINANCE_ROLES)
def cash_detail(request, pk):
    movement = _cash_movement(request, pk)
    return render(
        request,
        "finance/cash_detail.html",
        {"movement": movement, "company": request.company},
    )


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def cash_edit(request, pk):
    movement = _cash_movement(request, pk)
    if request.method == "POST":
        form = CashMovementForm(
            request.POST, company=request.company, user=request.user, instance=movement
        )
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except Exception as exc:
                messages.error(request, f"Não foi possível guardar: {exc}")
            else:
                messages.success(request, "Movimento atualizado.")
                return redirect(reverse("finance:cash_detail", kwargs={"pk": movement.pk}))
    else:
        form = CashMovementForm(
            company=request.company, user=request.user, instance=movement
        )
    return render(
        request,
        "finance/cash_form_edit.html",
        {"form": form, "movement": movement, "company": request.company},
    )


@login_required
@require_POST
@require_company
@require_roles(*FINANCE_ROLES)
def cash_delete(request, pk):
    movement = _cash_movement(request, pk)
    if movement.entry_allocations.exists():
        messages.error(
            request,
            "Não é possível excluir: este movimento está alocado a lançamentos (quitação).",
        )
        return redirect(reverse("finance:cash_detail", kwargs={"pk": pk}))
    memo = movement.memo or str(movement.movement_date)
    movement.delete()
    messages.success(request, f"Movimento removido ({memo}).")
    return redirect(reverse("finance:cash"))


@login_required
@require_http_methods(["GET", "POST"])
@require_company
@require_roles(*FINANCE_ROLES)
def cash_list(request):
    company = request.company
    ensure_default_categories(company)

    if request.method == "POST":
        form = CashMovementForm(request.POST, company=company, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    obj = form.save()
            except Exception as exc:
                messages.error(request, f"Não foi possível guardar: {exc}")
            else:
                messages.success(request, "Movimento guardado.")
                return redirect(reverse("finance:cash_detail", kwargs={"pk": obj.pk}))
    else:
        form = CashMovementForm(company=company, user=request.user)

    movements = (
        CashMovement.objects.filter(company=company)
        .select_related("financial_account", "payment_method")
        .order_by("-movement_date", "-pk")[:200]
    )

    accounts = FinancialAccount.objects.filter(company=company, is_active=True).order_by("name")
    balances = []
    for acc in accounts:
        qs = CashMovement.objects.filter(company=company, financial_account=acc)
        inc = qs.filter(kind__in=[CashMovementKind.RECEIPT, CashMovementKind.TRANSFER_IN]).aggregate(
            s=Coalesce(Sum("amount"), Decimal("0"))
        )["s"]
        out = qs.filter(
            kind__in=[CashMovementKind.PAYMENT, CashMovementKind.TRANSFER_OUT]
        ).aggregate(s=Coalesce(Sum("amount"), Decimal("0")))["s"]
        bal = inc - out
        balances.append({"account": acc, "balance": bal})

    return render(
        request,
        "finance/cash_list.html",
        {
            "form": form,
            "movements": movements,
            "balances": balances,
            "company": company,
        },
    )
