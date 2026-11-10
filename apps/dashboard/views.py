from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.models import MembershipRole
from apps.core.access import require_company
from apps.finance.services import ensure_default_categories

from .services import (
    chart_income_expense_months,
    chart_revenue_by_customer,
    chart_revenue_by_truck,
    dashboard_kpis,
    parse_dashboard_range,
)


@login_required
@require_company
def home(request):
    company = request.company
    membership = request.membership
    ensure_default_categories(company)

    start, end, range_mode = parse_dashboard_range(request.GET)
    kpis = dashboard_kpis(company, start, end)

    show_finance = membership.role != MembershipRole.DRIVER

    chart_m = chart_income_expense_months(company, months=6)
    chart_trucks = chart_revenue_by_truck(company, start, end)
    chart_customers = chart_revenue_by_customer(company, start, end)

    context = {
        "company": company,
        "membership": membership,
        "range_mode": range_mode,
        "period_start": start,
        "period_end": end,
        "kpis": kpis,
        "show_finance": show_finance,
        "chart_income_expense": chart_m,
        "chart_trucks": chart_trucks,
        "chart_customers": chart_customers,
    }
    return render(request, "dashboard/home.html", context)
