from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .models import Author, Post, Like

from datetime import datetime, timedelta, date, time
import pytz
from django.contrib import messages

from rest_framework.decorators import api_view
from rest_framework.response import Response

# Create your views here.
@login_required
def homepage(request):
    author = request.user.author
    return render(request=request,
                  template_name='main/home.html',
                  context={'user': request.user})

def login(request):
    return render(request=request,
                  template_name='main/login.html',
                  context={})


@api_view(['POST'])
def loginRequest(request):
    print("Login request received")

    username = request.data['username']
    password = request.data['password']

    user = authenticate(username=username, password=password)

    if user != None:
        auth_login(request, user)
        return HttpResponse(201)

    return HttpResponse(403)

@api_view(['GET'])
def logoutRequest(request):
    print("Logout request received")
    
    auth_logout(request)
    return HttpResponse(201)

@api_view(['POST'])
def makePost(request):
    print("Make-post request received")

    user = request.user
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
        post = Post(author=author, content=text, timestamp=datetime.now(pytz.timezone('America/Edmonton')), publicity=publicity, private_to=friends)
    else:
        post = Post(author=author, content=text, timestamp=datetime.now(pytz.timezone('America/Edmonton')), publicity=publicity)

    post.save()

    return HttpResponse(201)

@api_view(['GET'])
def getOldAvailablePosts(request):
    print("Get available posts request received")

    user = request.user
    author = Author.objects.get(user=user)
    
    posts = Post.objects.all().order_by('timestamp')[:10] #Change the 10 if we want more possible posts per feed

    data = {}
    i = 0
    for post in posts:
        liked = author.likes.filter(post=post)
        if len(liked) == 0:
            liked = 0
        else:
            liked = 1
        if post.publicity == 0:
            data[i] =[post.id, post.author.user.username, f"{post.timestamp.date().strftime('%Y-%m-%d')} {post.timestamp.time().strftime('%H:%M:%S')}", post.content, len(post.likes.all()), liked]
            i += 1
        elif post.publicity == 1:
            if author in post.private_to:
                data[i] = [post.id, post.author.user.username, f"{post.timestamp.date().strftime('%Y-%m-%d')} {post.timestamp.time().strftime('%H:%M:%S')}", post.content, len(post.likes.all()), liked]
                i += 1

    return JsonResponse(data)

@api_view(['GET'])
def getNewAvailablePosts(request):
    print("Get available posts request received")

    user = request.user
    author = Author.objects.get(user=user)

    oldDate = datetime.now(pytz.timezone('America/Edmonton')) - timedelta(seconds=5)
    
    posts = Post.objects.filter(timestamp__gte=oldDate).order_by('timestamp')[:10] #Change the 10 if we want more possible posts per feed

    data = {}
    i = 0
    for post in posts:
        liked = author.likes.filter(post=post)
        if len(liked) == 0:
            liked = 0
        else:
            liked = 1
        if post.publicity == 0:
            data[i] = [post.id, post.author.user.username, f"{post.timestamp.date().strftime('%Y-%m-%d')} {post.timestamp.time().strftime('%H:%M:%S')}", post.content, len(post.likes.all()), liked]
            i += 1
        elif post.publicity == 1:
            if author in post.private_to:
                data[i] = [post.id, post.author.user.username, f"{post.timestamp.date().strftime('%Y-%m-%d')} {post.timestamp.time().strftime('%H:%M:%S')}", post.content, len(post.likes.all()), liked]
                i += 1

    return JsonResponse(data)


@api_view(['GET'])
def htmlServiceFeedPost(request):
    print("Servicing the feedpost")

    with open('./socialsink/main/templates/includes/feedpost.html', 'r') as f:
        text = f.read()

    return FileResponse(file, content_type='text/html')

# delete account functionality, needs to be fine tuned
@api_view(['DELETE'])
def deleteAccount(request):
    # https://stackoverflow.com/questions/33715879/how-to-delete-user-in-django
    # https://docs.djangoproject.com/en/4.2/ref/contrib/messages/
    messages.info(request, "Delete-account request received.")

    user = request.user
    try:
        author = Author.objects.get(user=user)
        author.delete()
        messages.success(request, "The user has been deleted")  
        return HttpResponse(201)
    except Author.DoesNotExist:
        messages.error(request, "User does not exist")    
        return HttpResponse(404)
    except Exception as e: 
        return HttpResponse(403)
    
@api_view(['DELETE'])
def deletePost(request):
    messages.info(request, "Delete post request received.")

    user = request.user
    postID = int(request.data["id"])
    try:
        post = Post.objects.get(id=postID, author=user)
        post.delete()
        messages.success(request, "The post has been deleted")  
        return HttpResponse(201)
    except Post.DoesNotExist:
        messages.error(request, "Post does not exist")    
        return HttpResponse(404)
    except Exception as e: 
        return HttpResponse(403)

@api_view(['POST'])
def likePost(request, id):
    print("Like post request received")

    user = request.user

    try:
        post = Post.objects.get(id=id)
        author = Author.objects.get(user=user)
        like = Like(author=author, post=post, timestamp=datetime.now(pytz.timezone('America/Edmonton')))
        like.save()
        return HttpResponse(201)
    except Post.DoesNotExist:
        return HttpResponse(404)


@api_view(['DELETE'])
def unlikePost(request, id):
    print("Unlike Post request received")

    user = request.user 
    
    try:
        author = Author.objects.get(user=user)
        post = Post.objects.get(id=id)
        like = Like.objects.get(author=author, post=post)
        like.delete()
        return HttpResponse(201)
    except Post.DoesNotExist:
        return HttpResponse(404)


@api_view(['GET'])
def getLikeCount(request, id):
    print("Get Like Count request received")

    user = request.user
    
    try:
        post = Post.objects.get(id=id)
        count = len(post.likes.all())
        return HttpResponse(count)
    except Post.DoesNotExist:
        return HttpResponse(404)
