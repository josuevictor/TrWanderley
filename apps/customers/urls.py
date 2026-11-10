from django.urls import path

from . import views
from . import views_delivery_json

app_name = "customers"

urlpatterns = [
    path("", views.customer_list, name="list"),
    path("<int:pk>/locais-entrega.json", views_delivery_json.customer_delivery_places_json, name="delivery_places_json"),
    path("<int:pk>/", views.customer_detail, name="detail"),
    path("<int:pk>/editar/", views.customer_edit, name="edit"),
    path("<int:pk>/excluir/", views.customer_delete, name="delete"),
]
