from django.urls import path
from . import views

urlpatterns = [
    path("", views.login, name="login"),
    path("home/", views.homepage, name="homepage"),
    path("api/login/", views.loginRequest, name="loginRequest")
]