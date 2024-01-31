from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class ServerSettings(models.Model):
    id = models.AutoField(primary_key=True)
    auto_permit_users = models.BooleanField()


class Author(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.CharField(max_length=200, null=True)
    github = models.CharField(max_length=200, null=True, blank=True)
    profileImage = models.CharField(max_length=200, null=True, blank=True) #link to public image
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    is_permitted = models.BooleanField(default=True)


#only stores follows TO local authors, follows TO remote authors are stored in the remote author's server
# a friendship synonymous with a follow, a true friendship is when two authors follow each other
#TODO figure out how to allow foriegn keys to remote authors
class Follower(models.Model):
    id = models.AutoField(primary_key=True)
    follower_endpoint = models.CharField(max_length=1000, default='')
    follower_host = models.CharField(max_length=1000, default='')
    follower_data = models.CharField(max_length=2000, default='')
    followee_endpoint = models.CharField(max_length=1000, default='')
    followee_host = models.CharField(max_length=1000, default='')
    followee_data = models.CharField(max_length=2000, default='')
    dismissed = models.BooleanField(default=False) # false if followee has not yet viewed and dismissed the follow request, allows for "Friend Requests" DEPRECATED
    accepted = models.BooleanField(default=False) # This flag indicates if the follow request has been accepted. DEPRECATED
    friendship = models.BooleanField(default=False) # This flag indicates if there is a bidirectional follow (friend) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "dismissed: {} | accepted: {} | friendship: {}".format(self.dismissed.__str__(), self.accepted.__str__(), self.friendship.__str__())


class Post(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200, default="Default title")
    description = models.CharField(max_length=200, null=True)
    author_endpoint = models.CharField(max_length=1000, default='')
    author_data = models.CharField(max_length=2000, default='')
    contentType = models.CharField(max_length=200, default="text/plain")
    content = models.TextField()
    source = models.CharField(max_length=200, null=True) #Where did reposter get post from
    origin = models.CharField(max_length=200, null=True) #Where post is actually from
    categories = models.CharField(max_length=200, null=True) #comma separated list of categories
    image = models.ImageField(null=True, upload_to="images/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    publicity = models.IntegerField(default=0) # 2 = private, 1 = friends, 0 = public
    unlisted = models.BooleanField(default=False)


#TODO do we want to store comments from deleted authors?
class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    author_data = models.CharField(max_length=2000, default='')
    post_endpoint = models.CharField(max_length=1000, default='')
    content = models.CharField(max_length=600)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)


#our node has to store all likes on things it hosts, AND all likes from authors it hosts (including to other nodes)
#TODO do we want to store likes from deleted authors?
class Like(models.Model): 
    id = models.AutoField(primary_key=True)
    context = models.CharField(max_length=200, null=True) # i don't know what this is, but it's in the spec. @context
    author_endpoint = models.CharField(max_length=1000, default='')
    author_data = models.CharField(max_length=2000, default='')
    post_endpoint = models.CharField(max_length=1000, default='', null=True)
    summary = models.CharField(max_length=200, default='')
    comment_endpoint = models.CharField(max_length=1000, default='', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

# https://stackoverflow.com/questions/53461410/make-user-email-unique-django
User._meta.get_field('email')._unique = True


class Inbox(models.Model):
    id = models.AutoField(primary_key=True)
    endpoint = models.CharField(max_length=1000, default="")
    type = models.CharField(max_length=200, default="")
    author_id = models.CharField(max_length=1000, default='') #author who received the notification
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)


class Node(models.Model):
    id = models.AutoField(primary_key=True)
    hostname = models.CharField(max_length=200)
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)