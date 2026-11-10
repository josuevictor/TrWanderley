"""Acesso por empresa e perfil (membership ativo na sessão)."""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from apps.accounts.models import CompanyMembership, MembershipRole

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


def get_active_membership(request: HttpRequest) -> CompanyMembership | None:
    if not request.user.is_authenticated:
        return None
    qs = CompanyMembership.objects.filter(
        user=request.user,
        is_active=True,
    ).select_related("company")
    cid = request.session.get("active_company_id")
    if cid is None:
        lst = list(qs[:2])
        if len(lst) == 1:
            m = lst[0]
            request.session["active_company_id"] = m.company_id
            return m
        return None
    m = qs.filter(company_id=cid).first()
    if m is None:
        request.session.pop("active_company_id", None)
    return m


def redirect_no_company(request: HttpRequest) -> HttpResponse:
    messages.warning(
        request,
        "É necessário pertencer a uma empresa. Peça ao administrador ou configure no admin.",
    )
    return redirect(reverse("accounts:no_company"))


def redirect_no_access(request: HttpRequest) -> HttpResponse:
    messages.error(request, "Não tem permissão para aceder a esta área.")
    return redirect(reverse("dashboard:home"))


def require_company(view):
    """View function: exige membership válido; define request.company e request.membership."""

    @functools.wraps(view)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse("accounts:login"))
        m = get_active_membership(request)
        if m is None:
            return redirect_no_company(request)
        request.company = m.company  # type: ignore[attr-defined]
        request.membership = m  # type: ignore[attr-defined]
        return view(request, *args, **kwargs)

    return _wrapped


def require_roles(*roles):
    """Verifica perfil. Combinar com @require_company por fora (@require_company @require_roles ...)."""

    def decorator(view):
        @functools.wraps(view)
        def _wrapped(request, *args, **kwargs):
            m = getattr(request, "membership", None)
            if m is None:
                return redirect_no_company(request)
            if m.role not in roles:
                return redirect_no_access(request)
            return view(request, *args, **kwargs)

        return _wrapped

    return decorator


FINANCE_ROLES = (MembershipRole.ADMIN, MembershipRole.MANAGER)
OPS_ROLES = (MembershipRole.ADMIN, MembershipRole.MANAGER, MembershipRole.DRIVER)
