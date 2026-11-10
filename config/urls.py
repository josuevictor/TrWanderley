"""
URL configuration for caminhão-pipa.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("conta/", include("apps.accounts.urls")),
    path("financeiro/", include("apps.finance.urls")),
    path("frota/", include("apps.trucks.urls")),
    path("funcionarios/", include("apps.employees.urls")),
    path("clientes/", include("apps.customers.urls")),
    path("fornecedores/", include("apps.suppliers.urls")),
    path("viagens/", include("apps.trips.urls")),
    path("combustivel/", include("apps.fuel.urls")),
    path("manutencao/", include("apps.maintenance.urls")),
    path("", include("apps.dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
