from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .models import Author, Post
from datetime import datetime

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
        post = Post(author=author, content=text, timestamp=datetime.now(), publicity=publicity, private_to=friends)
    else:
        post = Post(author=author, content=text, timestamp=datetime.now(), publicity=publicity)

    post.save()

    return HttpResponse(201)