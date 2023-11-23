from django.contrib import admin
from .models import Author, Post, ServerSettings, Follower

# Register your models here.
admin.site.register(Author)
admin.site.register(Post)
admin.site.register(ServerSettings)
admin.site.register(Follower)