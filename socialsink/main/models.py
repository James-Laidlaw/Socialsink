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
    friends = models.ManyToManyField('self', symmetrical=False, through="Friendship", related_name='friend_set') #DEPRECATED
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    is_permitted = models.BooleanField(default=True)

#only stores follows TO local authors, follows TO remote authors are stored in the remote author's server
# a friendship synonymous with a follow, a true friendship is when two authors follow each other
#TODO figure out how to allow foriegn keys to remote authors
class Follower(models.Model):
    id = models.AutoField(primary_key=True)
    is_foreign = models.BooleanField(default=False) # true if the follow is to a remote author
    follower = models.ForeignKey(Author, related_name='following', on_delete=models.CASCADE, null=True)
    foreign_follower_id = models.CharField(max_length=200, null=True) # if is_foreign is true, this is the url of the foreign follower
    followee = models.ForeignKey(Author, related_name='followed_by', on_delete=models.CASCADE)
    dismissed = models.BooleanField(default=False) # false if followee has not yet viewed and dismissed the follow request, allows for "Friend Requests" DEPRECATED
    accepted = models.BooleanField(default=False) # This flag indicates if the follow request has been accepted. DEPRECATED
    friendship = models.BooleanField(default=False) # This flag indicates if there is a bidirectional follow (friend) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "id: {} | follower: {} | followee: {} | dismissed: {} | accepted: {} | friendship: {}".format(self.id.__str__(), self.follower.__str__(), 
                                                                                           self.followee.__str__(), self.dismissed.__str__(),
                                                                                           self.accepted.__str__(), self.friendship.__str__())

# TODO discuss if we need this. IMO it's redundant because a friendship is synonymous with a follow and a true friendship is just a bidirectional follow
class Friendship(models.Model): #DEPRECATED
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
    is_foreign = models.BooleanField(default=False) # true if the comment is to a remote post
    author_data = models.CharField(max_length=1000, default='')
    foreign_author_id = models.CharField(max_length=200, null=True) # if is_foreign is true, this is the url of the foreign author
    post_endpoint = models.CharField(max_length=1000, default='')
    content = models.CharField(max_length=600)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

#our node has to store all likes on things it hosts, AND all likes from authors it hosts (including to other nodes)
#TODO do we want to store likes from deleted authors?
class Like(models.Model): 
    id = models.AutoField(primary_key=True)
    context = models.CharField(max_length=200, null=True) # i don't know what this is, but it's in the spec. @context
    is_foreign = models.BooleanField(default=False) # true if the like is from a remote author
    author = models.ForeignKey(Author, related_name='likes', on_delete=models.CASCADE, null=True)
    foreign_author_id = models.CharField(max_length=200, null=True) # if is_foreign is true, this is the url of the foreign author
    post_endpoint = models.CharField(max_length=1000, default='')
    summary = models.CharField(max_length=200, default='')
    comment_endpoint = models.CharField(max_length=1000, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

# https://stackoverflow.com/questions/53461410/make-user-email-unique-django
User._meta.get_field('email')._unique = True


class Inbox(models.Model):
    id = models.AutoField(primary_key=True)
    endpoint = models.CharField(max_length=1000, default="")
    type = models.CharField(max_length=200, default="")
    #author who received the notification
    author = models.ForeignKey(Author, related_name='inbox', on_delete=models.CASCADE) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)


class Node(models.Model):
    id = models.AutoField(primary_key=True)
    hostname = models.CharField(max_length=200)
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)