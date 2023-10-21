from django.db import models

# Create your models here.

class Author(models.Model):
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=200) #TODO consider hashing
    follows = models.ManyToManyField('self', symmetrical=False, through='Follow', related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

#only stores follows FROM local authors, follows from remote authors are stored in the remote author's server
# a friendship is when two authors follow each other
class Follow(models.Model):
    follower = models.ForeignKey(Author, related_name='following', on_delete=models.CASCADE)
    followee = models.ForeignKey(Author, related_name='followed_by', on_delete=models.CASCADE)
    dismissed = models.BooleanField(default=False) # false if followee has not yet viewed and dismissed the follow request, allows for "Friend Requests"
    created_at = models.DateTimeField(auto_now_add=True)

class Post(models.Model):
    author = models.ForeignKey(Author, related_name='posts', on_delete=models.CASCADE)
    content = models.CharField(max_length=600)
    timestamp = models.DateTimeField('date published')
    publicity = models.IntegerField(default=0) # 0 = private, 1 = friends, 2 = public
    private_to = models.ForeignKey(Author, related_name='readable_by', null=True, on_delete=models.SET_NULL) # only used if publicity = 0

class Comment(models.Model):
    author = models.ForeignKey(Author, related_name='comments', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    content = models.CharField(max_length=600)
    timestamp = models.DateTimeField('date published')

class Like(models.Model): 
    author = models.ForeignKey(Author, related_name='likes', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)
    timestamp = models.DateTimeField('date published')
