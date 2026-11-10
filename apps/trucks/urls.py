from django.urls import path

from . import views

app_name = "trucks"

urlpatterns = [
    path("", views.truck_list, name="list"),
    path("<int:pk>/", views.truck_detail, name="detail"),
    path("<int:pk>/editar/", views.truck_edit, name="edit"),
    path("<int:pk>/excluir/", views.truck_delete, name="delete"),
]
