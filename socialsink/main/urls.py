from django.urls import path
from . import views

from rest_framework.schemas import get_schema_view
from django.views.generic import TemplateView

urlpatterns = [
    path('api_schema', get_schema_view(title='API Schema', description='Guide for the REST API'), name='api_schema'),
    path('docs/', TemplateView.as_view(template_name='docs.html', extra_context={'schema_url':'api_schema'}), name='swagger-ui'),
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
    path("api/get-deleted-posts/", views.getDeletedPosts, name="getDeletedPosts"),
]