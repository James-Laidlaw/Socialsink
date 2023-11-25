from django.contrib import admin
from .models import Author, Post, ServerSettings, Follower, Node, Inbox, Like, Comment

# Register your models here.
admin.site.register(Author)
admin.site.register(Post)
admin.site.register(ServerSettings)
admin.site.register(Follower)
admin.site.register(Node)
admin.site.register(Inbox)
admin.site.register(Like)
admin.site.register(Comment)