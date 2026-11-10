from django.urls import path

from . import views

app_name = "suppliers"

urlpatterns = [
    path("", views.supplier_list, name="list"),
    path("<int:pk>/", views.supplier_detail, name="detail"),
    path("<int:pk>/editar/", views.supplier_edit, name="edit"),
    path("<int:pk>/excluir/", views.supplier_delete, name="delete"),
]
