"""Template context — empresa ativa e empresas do utilizador."""

from apps.accounts.models import CompanyMembership


def _nav_active(request) -> str:
    """Chave para realçar item ativo no menu (prefixos dos URLconf)."""
    p = (getattr(request, "path", None) or "").rstrip("/")
    if p == "" or p == "/":
        return "dashboard"
    if p.startswith("/financeiro/receitas"):
        return "finance_receitas"
    segments = [
        ("/financeiro", "finance"),
        ("/frota", "trucks"),
        ("/funcionarios", "employees"),
        ("/clientes", "customers"),
        ("/fornecedores", "suppliers"),
        ("/manutencao", "maintenance"),
        ("/viagens", "finance_receitas"),
        ("/combustivel", "fuel"),
        ("/conta", ""),
    ]
    for prefix, key in segments:
        if p.startswith(prefix):
            return key
    return ""


def company_context(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {
            "current_company": None,
            "user_company_memberships": [],
        }

    memberships = list(
        CompanyMembership.objects.filter(user=request.user, is_active=True)
        .select_related("company")
        .order_by("company__name")
    )
    active_id = request.session.get("active_company_id")
    if active_id is None and len(memberships) == 1:
        request.session["active_company_id"] = memberships[0].company_id
        active_id = memberships[0].company_id
    current = None
    active_membership = None
    for m in memberships:
        if m.company_id == active_id:
            current = m.company
            active_membership = m
            break
    if current is None and memberships:
        current = memberships[0].company
        active_membership = memberships[0]

    return {
        "current_company": current,
        "user_company_memberships": memberships,
        "active_membership": active_membership,
        "nav_active": _nav_active(request),
    }
