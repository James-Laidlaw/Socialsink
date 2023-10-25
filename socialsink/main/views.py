from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.core.paginator import Paginator
from .models import Author, Post
from .serizlizers import AuthorSerializer

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


@api_view(['GET'])
#get list of authors with pagination
def getAuthors(request):
    pageNum = request.GET.get('page', 1)
    pageSize = request.GET.get('size', 50)

    authors = Author.objects.all()

    paginatedAuthors = Paginator(authors, pageSize)

    #paginator crashes if page number is out of range
    try: 
        page = paginatedAuthors.page(pageNum)
    except:
        return HttpResponse(404)


    author_serializer = AuthorSerializer(page, many=True, context={'request': request})

    serialized_authors = author_serializer.data

    return JsonResponse(serialized_authors, safe=False)

@api_view(['GET'])
def getAuthor(request, author_id):

    if author_id == None:
        return HttpResponse(400)
    
    author = Author.objects.get(id=author_id)

    if author == None:
        return HttpResponse(404)
    author_serializer = AuthorSerializer(author, context={'request': request})

    serialized_author = author_serializer.data
    return JsonResponse(serialized_author, safe=False)

@api_view(["POST"])
def updateAuthor(request, author_id):
    if author_id == None:
        return HttpResponse(400)

    author = Author.objects.get(id=author_id)

    if author == None:
        return HttpResponse(404)

    author_serializer = AuthorSerializer(author, data=request.data, partial=True)

    if author_serializer.is_valid():
        author_serializer.save()
        return HttpResponse(200)
    else:
        return HttpResponse(400)
    
    