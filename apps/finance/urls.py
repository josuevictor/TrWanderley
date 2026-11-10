from django.urls import path

from apps.trips import views as trip_views

from . import views

app_name = "finance"

urlpatterns = [
    path("", views.finance_home, name="home"),
    path("despesas/", views.expenses_hub, name="expenses"),
    path("configuracao/", views.finance_settings, name="settings"),
    path("receitas/", trip_views.trip_list, name="receitas"),
    path("receitas/<int:pk>/", trip_views.trip_detail, name="receitas_detail"),
    path("receitas/<int:pk>/editar/", trip_views.trip_edit, name="receitas_edit"),
    path("receitas/<int:pk>/excluir/", trip_views.trip_delete, name="receitas_delete"),
    path("categorias/", views.category_list, name="categories"),
    path("categorias/<int:pk>/", views.category_detail, name="category_detail"),
    path("categorias/<int:pk>/editar/", views.category_edit, name="category_edit"),
    path("categorias/<int:pk>/excluir/", views.category_delete, name="category_delete"),
    path("formas-pagamento/", views.payment_method_list, name="payment_methods"),
    path("formas-pagamento/<int:pk>/", views.payment_method_detail, name="payment_method_detail"),
    path(
        "formas-pagamento/<int:pk>/editar/",
        views.payment_method_edit,
        name="payment_method_edit",
    ),
    path(
        "formas-pagamento/<int:pk>/excluir/",
        views.payment_method_delete,
        name="payment_method_delete",
    ),
    path("contas/", views.account_list, name="accounts"),
    path("contas/<int:pk>/", views.account_detail, name="account_detail"),
    path("contas/<int:pk>/editar/", views.account_edit, name="account_edit"),
    path("contas/<int:pk>/excluir/", views.account_delete, name="account_delete"),
    path("lancamentos/", views.entry_list, name="entries"),
    path("lancamentos/<int:pk>/", views.entry_detail, name="entry_detail"),
    path("lancamentos/<int:pk>/editar/", views.entry_edit, name="entry_edit"),
    path("lancamentos/<int:pk>/excluir/", views.entry_delete, name="entry_delete"),
    path("caixa/", views.cash_list, name="cash"),
    path("caixa/<int:pk>/", views.cash_detail, name="cash_detail"),
    path("caixa/<int:pk>/editar/", views.cash_edit, name="cash_edit"),
    path("caixa/<int:pk>/excluir/", views.cash_delete, name="cash_delete"),
]
