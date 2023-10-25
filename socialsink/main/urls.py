from django.urls import path, re_path
from . import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("", views.homepage, name="homepage"),
    path("api/login/", views.loginRequest, name="loginRequest"),
    path("api/logout/", views.logoutRequest, name="logoutRequest"),
    path("api/make-post/", views.makePost, name="makePost"),
    path("service/authors/<str:author_id>/", views.getAuthor, name="authorDetail"),
    # https://stackoverflow.com/questions/1596552/django-urls-without-a-trailing-slash-do-not-redirect?rq=4
    re_path (r"^service/authors/?", views.getAuthors, name="authorList"), 
]