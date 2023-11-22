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
    follows = models.ManyToManyField('self', symmetrical=False, through="Follower", related_name='follower_set')
    friends = models.ManyToManyField('self', symmetrical=False, through="Friendship", related_name='friend_set')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    is_permitted = models.BooleanField(default=True)

#only stores follows TO local authors, follows TO remote authors are stored in the remote author's server
# a friendship synonymous with a follow, a true friendship is when two authors follow each other
#TODO figure out how to allow foriegn keys to remote authors
class Follower(models.Model):
    id = models.AutoField(primary_key=True)
    follower = models.ForeignKey(Author, related_name='following', on_delete=models.CASCADE)
    followee = models.ForeignKey(Author, related_name='followed_by', on_delete=models.CASCADE)
    dismissed = models.BooleanField(default=False) # false if followee has not yet viewed and dismissed the follow request, allows for "Friend Requests"
    accepted = models.BooleanField(default=False) # This flag indicates if the follow request has been accepted.
    friendship = models.BooleanField(default=False) # This flag indicates if there is a bidirectional follow (friend)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "id: {} | follower: {} | followee: {} | dismissed: {} | accepted: {} | friendship: {}".format(self.id.__str__(), self.follower.__str__(), 
                                                                                           self.followee.__str__(), self.dismissed.__str__(),
                                                                                           self.accepted.__str__(), self.friendship.__str__())

# TODO discuss if we need this. IMO it's redundant because a friendship is synonymous with a follow and a true friendship is just a bidirectional follow
class Friendship(models.Model):
    id = models.AutoField(primary_key=True)
    myself = models.ForeignKey(Author, related_name='outgoing_friends', on_delete=models.CASCADE)
    friend = models.ForeignKey(Author, related_name='incoming_friends', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

class Post(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200, default="Default title")
    description = models.CharField(max_length=200, null=True)
    author = models.ForeignKey(Author, related_name='posts', on_delete=models.CASCADE)
    contentType = models.CharField(max_length=200, default="text/plain")
    content = models.CharField(max_length=600)
    source = models.CharField(max_length=200, null=True) #Where did reposter get post from
    origin = models.CharField(max_length=200, null=True) #Where post is actually from
    categories = models.CharField(max_length=200, null=True) #comma separated list of categories
    image = models.ImageField(null=True, upload_to="images/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    edited = models.BooleanField(default=False)
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
