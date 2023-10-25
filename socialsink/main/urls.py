from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("", views.homepage, name="homepage"),
    path("api/login/", views.loginRequest, name="loginRequest"),
    path("api/logout/", views.logoutRequest, name="logoutRequest"),
    path("api/make-post/", views.makePost, name="makePost"),
    path("api/get-old-available-posts/", views.getOldAvailablePosts, name="getOldAvailablePosts"),
    path("api/get-new-available-posts/", views.getNewAvailablePosts, name="getNewAvailablePosts"),
    path("api/html-service/feedpost/", views.htmlServiceFeedPost, name="htmlServiceFeedPost"),
]