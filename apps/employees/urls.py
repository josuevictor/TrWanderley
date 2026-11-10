from django.urls import path

from . import views

app_name = "employees"

urlpatterns = [
    path("", views.employee_list, name="list"),
    path("<int:pk>/", views.employee_detail, name="detail"),
    path("<int:pk>/editar/", views.employee_edit, name="edit"),
    path("<int:pk>/excluir/", views.employee_delete, name="delete"),
]
