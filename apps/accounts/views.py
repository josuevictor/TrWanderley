from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from apps.core.access import get_active_membership

from .models import CompanyMembership


@login_required
@require_GET
def post_login_redirect(request):
    """Após login: painel se houver membership; senão página de orientação (evita redirect loop)."""
    if get_active_membership(request):
        return redirect(reverse("dashboard:home"))
    return redirect(reverse("accounts:no_company"))


@login_required
@require_GET
def no_company(request):
    """Utilizador autenticado sem empresa / membership válido."""
    memberships = CompanyMembership.objects.filter(user=request.user, is_active=True).select_related(
        "company"
    )
    return render(
        request,
        "accounts/no_company.html",
        {
            "memberships": memberships,
        },
    )


@login_required
@require_POST
def switch_company(request, company_id):
    """Define a empresa ativa na sessão (apenas membros)."""
    get_object_or_404(
        CompanyMembership,
        user=request.user,
        company_id=company_id,
        is_active=True,
    )
    request.session["active_company_id"] = company_id
    messages.success(request, "Empresa alterada.")
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect(reverse("dashboard:home"))
