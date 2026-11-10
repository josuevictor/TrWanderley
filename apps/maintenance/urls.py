from django.urls import path

from . import views

app_name = "maintenance"

urlpatterns = [
    path("", views.maintenance_list, name="list"),
    path("<int:pk>/", views.maintenance_detail, name="detail"),
    path("<int:pk>/editar/", views.maintenance_edit, name="edit"),
    path("<int:pk>/excluir/", views.maintenance_delete, name="delete"),
]
