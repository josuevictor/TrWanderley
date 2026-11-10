"""Agregações para o painel (KPIs e dados de gráficos)."""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.finance.models import (
    CashMovement,
    CashMovementKind,
    FinancialCategoryKind,
    FinancialEntry,
    FinancialEntryType,
    FinancialAccount,
)
from apps.trips.models import Trip
from apps.trucks.models import Truck, TruckStatus


def parse_dashboard_range(request_get) -> tuple[date, date, str]:
    """Intervalo [start, end] inclusive; devolve também o modo para o formulário."""
    today = timezone.localdate()
    mode = request_get.get("range", "month")

    if mode == "today":
        return today, today, mode
    if mode == "7d":
        start = today - timezone.timedelta(days=6)
        return start, today, mode
    if mode == "prev_month":
        first_this = today.replace(day=1)
        end_prev = first_this - timezone.timedelta(days=1)
        start_prev = end_prev.replace(day=1)
        return start_prev, end_prev, mode
    if mode == "year":
        return date(today.year, 1, 1), date(today.year, 12, 31), mode
    if mode == "custom":
        try:
            s = date.fromisoformat(request_get.get("from", ""))
            e = date.fromisoformat(request_get.get("to", ""))
            if s <= e:
                return s, e, mode
        except ValueError:
            pass
        mode = "month"
    # month (default)
    start = today.replace(day=1)
    _, last = monthrange(today.year, today.month)
    end = today.replace(day=last)
    return start, end, mode


def dashboard_kpis(company, start: date, end: date) -> dict:
    entries_period = FinancialEntry.objects.filter(
        company=company,
        is_cancelled=False,
        competence_date__gte=start,
        competence_date__lte=end,
    )

    invoiced_income = entries_period.filter(
        entry_type=FinancialEntryType.INCOME
    ).aggregate(t=Coalesce(Sum("amount"), Decimal("0")))["t"]

    expenses_comp = entries_period.filter(
        entry_type=FinancialEntryType.EXPENSE
    ).aggregate(t=Coalesce(Sum("amount"), Decimal("0")))["t"]

    received = CashMovement.objects.filter(
        company=company,
        kind=CashMovementKind.RECEIPT,
        movement_date__gte=start,
        movement_date__lte=end,
    ).aggregate(t=Coalesce(Sum("amount"), Decimal("0")))["t"]

    paid_out = CashMovement.objects.filter(
        company=company,
        kind=CashMovementKind.PAYMENT,
        movement_date__gte=start,
        movement_date__lte=end,
    ).aggregate(t=Coalesce(Sum("amount"), Decimal("0")))["t"]

    open_recv = Decimal("0")
    for e in FinancialEntry.objects.filter(
        company=company,
        is_cancelled=False,
        entry_type=FinancialEntryType.INCOME,
    ).select_related("category")[:5000]:
        open_recv += e.amount_open

    open_pay = Decimal("0")
    for e in FinancialEntry.objects.filter(
        company=company,
        is_cancelled=False,
        entry_type=FinancialEntryType.EXPENSE,
    ).select_related("category")[:5000]:
        open_pay += e.amount_open

    fuel_spend = entries_period.filter(
        entry_type=FinancialEntryType.EXPENSE,
        category__slug="fuel",
        category__kind=FinancialCategoryKind.EXPENSE,
    ).aggregate(t=Coalesce(Sum("amount"), Decimal("0")))["t"]

    maint_spend = entries_period.filter(
        entry_type=FinancialEntryType.EXPENSE,
        category__slug="maintenance",
        category__kind=FinancialCategoryKind.EXPENSE,
    ).aggregate(t=Coalesce(Sum("amount"), Decimal("0")))["t"]

    salary_spend = entries_period.filter(
        entry_type=FinancialEntryType.EXPENSE,
        category__slug="salary",
        category__kind=FinancialCategoryKind.EXPENSE,
    ).aggregate(t=Coalesce(Sum("amount"), Decimal("0")))["t"]

    # Soma do campo «quantidade de viagens» por registo, não o nº de linhas na tabela
    trip_count = (
        Trip.objects.filter(company=company, trip_date__gte=start, trip_date__lte=end).aggregate(
            t=Coalesce(Sum("trip_count"), Value(0))
        )["t"]
    )

    trucks_active = Truck.objects.filter(
        company=company, status=TruckStatus.ACTIVE
    ).count()
    trucks_maint = Truck.objects.filter(
        company=company, status=TruckStatus.MAINTENANCE
    ).count()

    operating_profit = invoiced_income - expenses_comp

    cash_balance = Decimal("0")
    for acc in FinancialAccount.objects.filter(company=company, is_active=True):
        qs = CashMovement.objects.filter(company=company, financial_account=acc)
        inc = qs.filter(
            kind__in=[CashMovementKind.RECEIPT, CashMovementKind.TRANSFER_IN]
        ).aggregate(s=Coalesce(Sum("amount"), Decimal("0")))["s"]
        out = qs.filter(
            kind__in=[CashMovementKind.PAYMENT, CashMovementKind.TRANSFER_OUT]
        ).aggregate(s=Coalesce(Sum("amount"), Decimal("0")))["s"]
        cash_balance += inc - out

    return {
        "invoiced_income": invoiced_income,
        "received_cash": received,
        "expenses_competence": expenses_comp,
        "paid_cash": paid_out,
        "open_receivables": open_recv,
        "open_payables": open_pay,
        "operating_profit": operating_profit,
        "cash_balance": cash_balance,
        "trip_count": trip_count,
        "trucks_active": trucks_active,
        "trucks_maintenance": trucks_maint,
        "fuel_spend": fuel_spend,
        "maintenance_spend": maint_spend,
        "salary_spend": salary_spend,
    }


def chart_income_expense_months(company, months: int = 6) -> dict:
    """Últimos `months` meses completos até ao mês atual."""
    today = timezone.localdate()
    labels = []
    income = []
    expense = []
    y, m = today.year, today.month
    for _ in range(months):
        _, last = monthrange(y, m)
        start = date(y, m, 1)
        end = date(y, m, last)
        labels.insert(0, f"{m:02d}/{y}")
        inc = FinancialEntry.objects.filter(
            company=company,
            is_cancelled=False,
            entry_type=FinancialEntryType.INCOME,
            competence_date__gte=start,
            competence_date__lte=end,
        ).aggregate(t=Coalesce(Sum("amount"), Decimal("0")))["t"]
        exp = FinancialEntry.objects.filter(
            company=company,
            is_cancelled=False,
            entry_type=FinancialEntryType.EXPENSE,
            competence_date__gte=start,
            competence_date__lte=end,
        ).aggregate(t=Coalesce(Sum("amount"), Decimal("0")))["t"]
        income.insert(0, float(inc))
        expense.insert(0, float(exp))
        if m == 1:
            m = 12
            y -= 1
        else:
            m -= 1
    return {"labels": labels, "income": income, "expense": expense}


def chart_revenue_by_truck(company, start: date, end: date, limit: int = 8) -> dict:
    rows = (
        Trip.objects.filter(company=company, trip_date__gte=start, trip_date__lte=end)
        .values("truck__plate")
        .annotate(total=Coalesce(Sum("amount_charged"), Decimal("0")))
        .order_by("-total")[:limit]
    )
    labels = [r["truck__plate"] or "—" for r in rows]
    data = [float(r["total"]) for r in rows]
    return {"labels": labels, "data": data}


def chart_revenue_by_customer(company, start: date, end: date, limit: int = 8) -> dict:
    rows = (
        Trip.objects.filter(company=company, trip_date__gte=start, trip_date__lte=end)
        .values("customer__name")
        .annotate(total=Coalesce(Sum("amount_charged"), Decimal("0")))
        .order_by("-total")[:limit]
    )
    labels = [r["customer__name"] or "—" for r in rows]
    data = [float(r["total"]) for r in rows]
    return {"labels": labels, "data": data}
