"""Rotas legadas /viagens/ — redirecionam para /financeiro/receitas/ (exceto POST excluir)."""

from django.shortcuts import redirect
from django.urls import path

from . import views as trip_views


def _redirect_receitas_list(request):
    return redirect("finance:receitas")


def _redirect_receitas_detail(request, pk):
    return redirect("finance:receitas_detail", pk=pk)


def _redirect_receitas_edit(request, pk):
    return redirect("finance:receitas_edit", pk=pk)


app_name = "trips"

urlpatterns = [
    path("", _redirect_receitas_list, name="list"),
    path("<int:pk>/", _redirect_receitas_detail, name="detail"),
    path("<int:pk>/editar/", _redirect_receitas_edit, name="edit"),
    path("<int:pk>/excluir/", trip_views.trip_delete, name="delete"),
]
