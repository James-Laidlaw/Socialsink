from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("", views.homepage, name="homepage"),
    path("api/login/", views.loginRequest, name="loginRequest"),
    path("api/logout/", views.logoutRequest, name="logoutRequest")
]