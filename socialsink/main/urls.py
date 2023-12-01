from django.urls import path, re_path
from . import views

from rest_framework.schemas import get_schema_view
from django.views.generic import TemplateView


urlpatterns = [
    path('api_schema', get_schema_view(title='API Schema', description='Guide for the REST API'), name='api_schema'),
    path('docs/', TemplateView.as_view(template_name='docs.html', extra_context={'schema_url':'api_schema'}), name='swagger-ui'),
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("posts/<str:id>", views.displayPost, name="displayPost"),
    path("", views.homepage, name="homepage"),
    path("api/login/", views.loginRequest, name="loginRequest"),
    path("api/logout/", views.logoutRequest, name="logoutRequest"),
    path("api/register/", views.createAccount, name="createAccount"),
    path("api/delete-account/", views.deleteAccount, name="deleteAccount"),
    path("api/update-user/<int:id>", views.updateUser, name="updateUser"),
    path("api/get-node-hosts/", views.getNodeHosts, name="getNodeHosts"),
    path("api/delete-inbox-item/<str:author_id>/posts/<str:post_id>", views.deleteInboxPost, name="deleteInboxPost"),
    path("api/create-comment-data/", views.createCommentData, name="createCommentData"),
    path("authors/<str:author_id>", views.authorReqHandler, name="authorReqHandler"),
    path("authors/", views.getAuthors, name="authorList"),
    path("authors/<str:author_id>/followers", views.getFollowers, name="getFollowers"),
    path("authors/<str:author_id>/followers/requests", views.getFollowRequests, name="getFollowRequests"),
    path("authors/<str:author_id>/following", views.getFollowing, name="getFollowing"),
    path("authors/<str:author_id>/friends", views.getFriends, name="getFriends"),
    path("authors/<str:author_id>/followers/<str:foreign_author_id>", views.followerReqHandler, name="followerReqHandler"),
    path("authors/<str:author_id>/posts/<str:post_id>", views.postReqHandler, name="postReqHandler"),
    path("authors/<str:author_id>/posts", views.postCreationReqHandler, name="postCreationReqHandler"),
    path("authors/<str:author_id>/posts/<str:post_id>/comments", views.commentReqHandler, name="commentReqHandler"),
    path("authors/<str:author_id>/inbox", views.inboxReqHandler, name="inboxReqHandler"),
    path("authors/<str:author_id>/posts/<str:post_id>/likes", views.getPostLikes, name="likeReqHandler"),
    path("authors/<str:author_id>/posts/<str:post_id>/comments/<str:comment_id>/likes", views.getCommentLikes, name="commentLikeReqHandler"),
    path("authors/<str:author_id>/liked", views.getAuthorLiked, name="authorLikedReqHandler"),
]