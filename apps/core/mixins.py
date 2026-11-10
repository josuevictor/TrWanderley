"""Reusable class-based view mixins."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse

from apps.accounts.models import CompanyMembership


class ActiveCompanyRequiredMixin(LoginRequiredMixin):
    """
    Utilizador autenticado + empresa ativa na sessão com membership válido.

    Expõe self.company e self.membership antes de get/post.
    """

    membership = None
    company = None

    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin: redirect se não autenticado
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        cid = request.session.get("active_company_id")
        if cid is None:
            messages.warning(request, "Selecione uma empresa para continuar.")
            return redirect(reverse("dashboard:home"))

        membership = (
            CompanyMembership.objects.filter(
                user=request.user,
                company_id=cid,
                is_active=True,
            )
            .select_related("company")
            .first()
        )
        if membership is None:
            request.session.pop("active_company_id", None)
            messages.error(request, "Sem acesso a esta empresa.")
            return redirect(reverse("dashboard:home"))

        self.membership = membership
        self.company = membership.company
        return super().dispatch(request, *args, **kwargs)
