from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Author(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    follows = models.ManyToManyField('self', symmetrical=False, through="Follower", related_name='follower_set')
    friends = models.ManyToManyField('self', symmetrical=False, through="Friendship", related_name='friend_set')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

#only stores follows FROM local authors, follows from remote authors are stored in the remote author's server
# a friendship is when two authors follow each other
class Follower(models.Model):
    id = models.AutoField(primary_key=True)
    follower = models.ForeignKey(Author, related_name='following', on_delete=models.CASCADE)
    followee = models.ForeignKey(Author, related_name='followed_by', on_delete=models.CASCADE)
    dismissed = models.BooleanField(default=False) # false if followee has not yet viewed and dismissed the follow request, allows for "Friend Requests"
    accepted = models.BooleanField(default=False) # This is a flag for informing the server if their is a mutual following or not
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

class Friendship(models.Model):
    id = models.AutoField(primary_key=True)
    myself = models.ForeignKey(Author, related_name='outgoing_friends', on_delete=models.CASCADE)
    friend = models.ForeignKey(Author, related_name='incoming_friends', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

class Post(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(Author, related_name='posts', on_delete=models.CASCADE)
    content = models.CharField(max_length=600)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    publicity = models.IntegerField(default=0) # 2 = private, 1 = friends, 0 = public
    private_to = models.ForeignKey(Author, related_name='readable_by', null=True, on_delete=models.SET_NULL) # only used if publicity = 0

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(Author, related_name='comments', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    content = models.CharField(max_length=600)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

class Like(models.Model): 
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(Author, related_name='likes', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE, null=True)
    comment = models.ForeignKey(Comment, related_name='likes', on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

# https://stackoverflow.com/questions/53461410/make-user-email-unique-django
User._meta.get_field('email')._unique = True