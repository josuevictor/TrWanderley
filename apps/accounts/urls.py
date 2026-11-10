from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import TailwindAuthenticationForm

app_name = "accounts"

urlpatterns = [
    path("apos-login/", views.post_login_redirect, name="post_login"),
    path("sem-empresa/", views.no_company, name="no_company"),
    path(
        "entrar/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=TailwindAuthenticationForm,
        ),
        name="login",
    ),
    path(
        "sair/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path(
        "empresa/<int:company_id>/trocar/",
        views.switch_company,
        name="switch_company",
    ),
]
