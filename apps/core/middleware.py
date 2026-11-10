"""HTTP middleware — empresa ativa na sessão."""

from django.utils.functional import SimpleLazyObject

from apps.accounts.models import CompanyMembership


def _resolve_current_company(request):
    """Return Company or None for authenticated users."""
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return None

    cid = request.session.get("active_company_id")
    if cid is not None:
        membership = (
            CompanyMembership.objects.filter(
                user=request.user,
                company_id=cid,
                is_active=True,
            )
            .select_related("company")
            .first()
        )
        if membership:
            return membership.company
        request.session.pop("active_company_id", None)

    first = (
        CompanyMembership.objects.filter(user=request.user, is_active=True)
        .select_related("company")
        .order_by("company__name")
        .first()
    )
    if first:
        request.session["active_company_id"] = first.company_id
        return first.company
    return None


class ActiveCompanyMiddleware:
    """Attach request.current_company (lazy) after authentication."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_company = SimpleLazyObject(lambda: _resolve_current_company(request))
        return self.get_response(request)
