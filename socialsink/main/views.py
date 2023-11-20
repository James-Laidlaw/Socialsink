from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .models import Author, Post, Like, Follower
from .serizlizers import AuthorSerializer

from datetime import datetime, timedelta, date, time
import pytz
from django.contrib import messages

from rest_framework.decorators import api_view
from rest_framework.response import Response

# Create your views here.
@login_required
def homepage(request):
    print(request.user)
    author = request.user.author
    return render(request=request,
                  template_name='main/home.html',
                  context={'user': request.user})

def login(request):
    return render(request=request,
                  template_name='main/login.html',
                  context={})

def register(request):
    return render(request=request,
                  template_name='main/register.html',
                  context={})

@api_view(['PUT'])
def createAccount(request):
    print("Registration request received")

    username = request.data['username']
    email = request.data['email']
    password = request.data['password']

    try:    
        user = User.objects.create_user(username=username, email=email, password=password)
        author = Author(user=user, created_at=datetime.now(pytz.timezone('America/Edmonton')))
        author.save()
        user.author = author
        user.save()

        auth_login(request, user)
        return Response(status=201)
        
    except:
        return Response(status=401)

@api_view(['POST'])
def loginRequest(request):
    print("Login request received")

    username = request.data['username']
    password = request.data['password']

    user = authenticate(username=username, password=password)

    if user != None:
        auth_login(request, user)
        return Response(status=201)

    return Response(status=401)

@api_view(['GET'])
def logoutRequest(request):
    print("Logout request received")
    
    auth_logout(request)
    return Response(status=200)

@api_view(['POST'])
def makePost(request):
    print("Make-post request received")

    user = request.user
    if user.is_authenticated:
        text = request.data['text']
        publicity = request.data['publicity']

        if publicity == 'public':
            publicity = 0
        elif publicity == 'friends':
            publicity = 1
        elif publicity == 'private':
            publicity = 2
        else:
            publicity = -1 #Unknown publicity

        author = Author.objects.get(user=user)
        if publicity == 1:
            author = Author.objects.get(user=user)
            friends = author.friend_set.all()
            post = Post(author=author, content=text, created_at=datetime.now(pytz.timezone('America/Edmonton')), publicity=publicity, private_to=friends)
        else:
            post = Post(author=author, content=text, created_at=datetime.now(pytz.timezone('America/Edmonton')), publicity=publicity)

        post.save()

        return Response(status=201)
    
    else:
        return Response(status=401)

@api_view(['GET'])
def getOldAvailablePosts(request):
    print("Get available posts request received")

    user = request.user
    if user.is_authenticated:
        author = Author.objects.get(user=user)
        
        posts = Post.objects.all().order_by('created_at')[:10] #Change the 10 if we want more possible posts per feed

        data = {}
        i = 0
        for post in posts:
            liked = author.likes.filter(post=post)

            if len(liked) == 0:
                liked = 0
            else:
                liked = 1

            isOwnPost = 0
            if post.author == author:
                isOwnPost = 1

            if post.publicity == 0:
                data[i] =[post.id, post.author.user.username, f"{post.created_at.date().strftime('%Y-%m-%d')} {post.created_at.time().strftime('%H:%M:%S')}", post.content, len(post.likes.all()), liked, isOwnPost]
                i += 1
            elif post.publicity == 1:
                if author in post.private_to:
                    data[i] = [post.id, post.author.user.username, f"{post.created_at.date().strftime('%Y-%m-%d')} {post.created_at.time().strftime('%H:%M:%S')}", post.content, len(post.likes.all()), liked, isOwnPost]
                    i += 1

        return Response(data, status=200)

    else:
        return Response(status=401)

@api_view(['GET'])
def getNewAvailablePosts(request):
    print("Get available posts request received")

    user = request.user
    if user.is_authenticated:
        author = Author.objects.get(user=user)

        oldDate = datetime.now(pytz.timezone('America/Edmonton')) - timedelta(seconds=5)
        
        posts = Post.objects.filter(created_at__gte=oldDate).order_by('created_at')[:10] #Change the 10 if we want more possible posts per feed

        data = {}
        i = 0
        for post in posts:
            liked = author.likes.filter(post=post)
            if len(liked) == 0:
                liked = 0
            else:
                liked = 1

            isOwnPost = 0
            if post.author == author:
                isOwnPost = 1

            if post.publicity == 0:
                data[i] = [post.id, post.author.user.username, f"{post.created_at.date().strftime('%Y-%m-%d')} {post.created_at.time().strftime('%H:%M:%S')}", post.content, len(post.likes.all()), liked, isOwnPost]
                i += 1
            elif post.publicity == 1:
                if author in post.private_to:
                    data[i] = [post.id, post.author.user.username, f"{post.created_at.date().strftime('%Y-%m-%d')} {post.created_at.time().strftime('%H:%M:%S')}", post.content, len(post.likes.all()), liked, isOwnPost]

        return Response(data, status=200)

    else:
        return Response(status=401)


# delete account functionality, needs to be fine tuned
@api_view(['DELETE'])
def deleteAccount(request):
    # https://stackoverflow.com/questions/33715879/how-to-delete-user-in-django
    # https://docs.djangoproject.com/en/4.2/ref/contrib/messages/
    messages.info(request, "Delete-account request received.")

    user = request.user
    if user.is_authenticated:
        try:
            author = Author.objects.get(user=user)
            author.delete()
            messages.success(request, "The user has been deleted")  
            return Response(status=200)
        except Author.DoesNotExist:
            messages.error(request, "User does not exist")    
            return Response(status=404)
        except Exception as e: 
            return Response(status=500)

    else:
        return Response(status=401)
    
@api_view(['DELETE'])
def deletePost(request, id):
    print("Delete post request received")

    user = request.user
    
    if user.is_authenticated:
        try:
            author = Author.objects.get(user=user)
            post = Post.objects.get(id=id, author=author)
            post.delete()
            messages.success(request, "The post has been deleted")  
            return Response(status=200)
        except Post.DoesNotExist:
            messages.error(request, "Post does not exist")    
            return Response(status=404)
        except Exception as e: 
            return Response(status=500)

    else:
        return Response(status=401)

@api_view(['POST'])
def likePost(request, id):
    print("Like post request received")

    user = request.user
    if user.is_authenticated:
    
        try:
            post = Post.objects.get(id=id)
            author = Author.objects.get(user=user)
            like = Like(author=author, post=post, created_at=datetime.now(pytz.timezone('America/Edmonton')))
            like.save()
            return Response(status=201)
        except Post.DoesNotExist:
            return Response(status=404)
        
    else:
        return Response(status=401)


@api_view(['DELETE'])
def unlikePost(request, id):
    print("Unlike Post request received")

    user = request.user 
    if user.is_authenticated:
    
        try:
            author = Author.objects.get(user=user)
            post = Post.objects.get(id=id)
            like = Like.objects.get(author=author, post=post)
            like.delete()
            return Response(status=200)
        except Post.DoesNotExist:
            return Response(status=404)

    else:
        return Response(status=401)


@api_view(['GET'])
def getLikeCount(request, id):
    print("Get Like Count request received")

    user = request.user
    if user.is_authenticated:
    
        try:
            post = Post.objects.get(id=id)
            count = len(post.likes.all())
            data = {'count': count}
            return Response(data, status=200)
        except Post.DoesNotExist:
            return Response(status=404)
    else:
        return Response(status=401)


@api_view(['GET'])
def getDeletedPosts(request):
    print("Get Deleted Posts request received")

    user = request.user
    if user.is_authenticated:
        
        ids = list(request.query_params.getlist('ids[]'))
        data = {}
        for i in range(len(ids)):
            if not Post.objects.filter(id=int(ids[i])):
                data[i] = int(ids[i])

        return Response(data, status=200)
    else:
        return Response(status=401)


@api_view(['GET'])
def getFollowing(request):
    user = request.user
    if user.is_authenticated:
        author = Author.objects.get(user=user)
        #### TESTING ####
        # Follower.objects.create(follower = author, followee = author, accepted = True)
        #### TESTING ####
        # print("Author follows:", author.follows.all())
        data = {}
        for i, follow in enumerate(author.follows.all()):
            data[i] = [follow.id, follow.user.username]
        return Response(data, status=200)

# TODO implement friendship checking and request sending
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def handleFollow(request):
    user = request.user
    if user.is_authenticated:
        author = Author.objects.get(user=user)
        
        # retrieving follow requests
        if request.method == 'GET':
            # Requests that not accepted and not dismissed
            follow_requests = [x for x in Follower.objects.filter(followee = author) if (not x.dismissed and not x.accepted)]
            data = {}
            for i, follow_request in enumerate(follow_requests):
                data[i] = {'id': follow_request.follower.id, 'user': follow_request.follower.user.username}
            return Response(data, status=200)

        # accept/dismiss follow request
        elif request.method == 'POST':
            if request.data['action'] == 'accept':
                pass
            elif request.data['action'] == 'dismiss':
                id = request.data['id']
                follower = Author.objects.get(id=id)
                follow_obj = Follower.objects.get(follower = follower, followee = author)
                print(follow_obj)
                follow_obj.dismissed = True
                follow_obj.save()
                return Response(status=200)
        
        # put follow request
        elif request.method == 'PUT':
            # id = request.data['id'].split('/')[-2]
            id = request.data['id']
            followee = Author.objects.get(id=id)
            Follower(follower = author, followee = followee, dismissed = False, accepted = False).save()
            return Response(status=200)
        
        # Used to consider unfollow and dismissal as the same operation,
        # moving dismissal to POST
        elif request.method == 'DELETE':
            # id = request.data['id'].split('/')[-2]
            id = request.data['id']
            print("FOLLOW DELETE",id)
            followee = Author.objects.get(id=id)
            Follower.objects.get(follower = author, followee = followee).delete()
            return Response(status=200)


# outwards facing API endpoints
@api_view(['GET'])
#get list of authors with pagination
def getAuthors(request):
    print("service: Get authors request received")
    pageNum = request.GET.get('page', 1)
    pageSize = request.GET.get('size', 50)

    authors = Author.objects.all().order_by('id')

    paginatedAuthors = Paginator(authors, pageSize)

    #paginator crashes if page number is out of range
    try: 
        page = paginatedAuthors.page(pageNum)
    except:
        return Response(status=404)


    author_serializer = AuthorSerializer(page, many=True, context={'request': request})

    serialized_authors = author_serializer.data

    return Response(serialized_authors)



@api_view(['GET', 'POST'])
def authorDetail(request, author_id):

    if request.method == 'GET': 
        print("service: Get author request received")
        return getAuthor(request, author_id)
    elif request.method == 'POST':
        print("service: Update author request received")
        return updateAuthor(request, author_id)
    else:
        return Response(status=405)



# get a single author by id
def getAuthor(request, author_id):
    if author_id == None:
        return Response(status=400)
    
    author = Author.objects.get(id=author_id)

    if author == None:
        return Response(status=404)
    author_serializer = AuthorSerializer(author, context={'request': request})

    serialized_author = author_serializer.data
    return Response(serialized_author)

# update an author by id
def updateAuthor(request, author_id):  
    if author_id == None:
        return Response(status=400)

    author = Author.objects.get(id=author_id)

    if author == None:
        return Response(status=404)
    
    #check authorization
    if author.user != request.user or not request.user.is_authenticated:
     print("unauthorized, returning 401")
     return Response(status=401)

    author_serializer = AuthorSerializer(author, data=request.data, partial=True)

    if author_serializer.is_valid():
        author_serializer.save()
        print(request.data)
        print(author_serializer.data)
        return Response(status=200)
    else:
        return Response(status=400)
