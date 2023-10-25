from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("", views.homepage, name="homepage"),
    path("api/login/", views.loginRequest, name="loginRequest"),
    path("api/logout/", views.logoutRequest, name="logoutRequest"),
    path("api/make-post/", views.makePost, name="makePost"),
    path("api/delete-account/", views.deleteAccount, name="deleteAccount"),
    path("api/delete-post/", views.deletePost, name="deletePost"),
]