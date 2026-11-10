from django.urls import path

from . import views

app_name = "fuel"

urlpatterns = [
    path("", views.fuel_list, name="list"),
    path("<int:pk>/", views.fuel_detail, name="detail"),
    path("<int:pk>/editar/", views.fuel_edit, name="edit"),
    path("<int:pk>/excluir/", views.fuel_delete, name="delete"),
]
