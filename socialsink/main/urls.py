from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("", views.homepage, name="homepage"),
    path("api/login/", views.loginRequest, name="loginRequest"),
    path("api/logout/", views.logoutRequest, name="logoutRequest"),
    path("api/register/", views.createAccount, name="createAccount"),
    path("api/make-post/", views.makePost, name="makePost"),
    path("api/delete-account/", views.deleteAccount, name="deleteAccount"),
    path("api/delete-post/<int:id>", views.deletePost, name="deletePost"),
    path("api/get-old-available-posts/", views.getOldAvailablePosts, name="getOldAvailablePosts"),
    path("api/get-new-available-posts/", views.getNewAvailablePosts, name="getNewAvailablePosts"),
    path("api/like-post/<int:id>", views.likePost, name="likePost"),
    path("api/unlike-post/<int:id>", views.unlikePost, name="unlikePost"),
    path("api/get-like-count/<int:id>", views.getLikeCount, name="getLikeCount"),
]