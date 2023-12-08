from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Author, Post, Like, Follower, ServerSettings, Comment, Inbox, Node
from .serizlizers import AuthorSerializer, PostSerializer, CommentSerializer, LikeSerializer, InboxSerializer, get_object_id_from_url

from datetime import datetime, timedelta, date, time
import pytz
from django.contrib import messages
from django.urls import reverse


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request

#Image Imports
from django.core.files.base import ContentFile
import base64
from PIL import Image
from io import BytesIO
import json
import re

# Create your views here.
@login_required
def homepage(request):
    # get author object from user
    author = Author.objects.get(user=request.user)

    # get the author serializer
    author_serializer = AuthorSerializer(author, context={'request': request})
    # get a dictionary of the author object
    serialized_author = author_serializer.data

    # render the homepage with the given context
    return render(request=request,
                  template_name='main/home.html',
                  context={'user': request.user,
                           'author': author,
                           'author_endpoint': serialized_author['id']})


def login(request):
    # render the login page without any context
    return render(request=request,
                  template_name='main/login.html',
            
                  context={})


def register(request):
    # render the register page without any context
    return render(request=request,
                  template_name='main/register.html',
                  context={})


def displayPost(request, id):
    # get user from the request
    user = request.user
    # only proceed if the user is authenticated
    if user.is_authenticated:

        author = Author.objects.get(user=user)
        
        # get the first post
        post = Post.objects.get(id=id)
        post_author = post.author_endpoint

        if post == None:
            # no posts, redirect to homepage
            return redirect('/')
          
        author_endpoint = request.build_absolute_uri(reverse('authorReqHandler', args=[author.id]))

        if post_author != author_endpoint:
            # assume post is not a friends only post
            permission = False
            following = Follower.objects.filter(follower_endpoint=author_endpoint, followee_endpoint=post_author).first()
             # if f is friends with author, permission is true
            if following and following.friendship == True:
                permission = True
                
            # if post is public and not a friends only post, redirect to homepage
            if post.publicity == 1 and not permission:
                return redirect('/')

        post_endpoint = request.build_absolute_uri(reverse('postReqHandler', args=[post.author_endpoint.split('/')[-1], post.id]))

        # render post.html with the given context (post data, like count, whether author liked it, and author)
        return render(request=request,
                      template_name='main/post.html',
                      context={
                        'post_endpoint': post_endpoint,
                        'author': author,
                        'author_endpoint': author_endpoint
                      })
        
    # if the user is not authenticated, redirect them to the login page
    else:
        return redirect('/login/')


def getAuthed(auth_header):
    # if there is no auth header attached, respond with a 401
    if not len(auth_header):
        return Response({"Unauthorized."}, status=401)
    token_type, _, credentials = auth_header.partition(' ')
    try:
        # split and decode from base 64 the username and password from 'credentials'
        username, password = base64.b64decode(credentials).decode().split(':')
        # get the first node that matches the username and the password
        node = Node.objects.filter(username=username, password=password).first()
        # if there is no such node, respond with a 401
        if node == None:
            return Response("Error decoding Authorization header", status=401)
        
        # if the node is socialsink (us), return self
        if node.username == 'socialsink':
            return 'self'
        else:
            return 'other'

    except:
        return Response("Error decoding Authorization header", status=400)


@api_view(['PUT'])
def createAccount(request):
    # get username, email, and password from the request
    username = request.data['username']
    email = request.data['email']
    password = request.data['password']
    
    # get the first server setting
    ss = ServerSettings.objects.first()
    # get the user that matches up with the criteria obtained from the request
    user = User.objects.create_user(username=username, email=email, password=password)
    
    # create an author based on whether the server is setup to auto permit users or not
    if ss.auto_permit_users == True:
        author = Author(user=user, created_at=datetime.now(pytz.timezone('America/Edmonton')))
    else:
        author = Author(user=user, created_at=datetime.now(pytz.timezone('America/Edmonton')), is_permitted=False)
    author.save()
    user.author = author
    user.save()

    if ss.auto_permit_users == True:
        # if auto permit is true, login the user
        auth_login(request, user)
    else:
        # if not, respond with a 301
        return Response(status=301)
    # respond with a 201
    return Response(status=201)


@api_view(['POST'])
def loginRequest(request):
    # get the username and password from the request
    username = request.data['username']
    password = request.data['password']

    # authenticate user with username and password provided
    user = authenticate(username=username, password=password)
    # get the author from the user
    author = Author.objects.get(user=user)
    if author.is_permitted:
        if user != None:
            # if the author is permitted and the authentication was successful,
            # login the user and respond with a 201
            auth_login(request, user)
            return Response(status=201)
    else:
        # if the author is not permitted, respond with a 301
        return Response(status=301)

    # if the author is permitted but the authentication was not successful, respond with a 401
    return Response(status=401)

@api_view(['GET'])
def logoutRequest(request):
    # logout the user and respond with 200
    auth_logout(request)
    return Response(status=200)


# delete account functionality, needs to be fine tuned
@api_view(['DELETE'])
def deleteAccount(request):
    # https://stackoverflow.com/questions/33715879/how-to-delete-user-in-django
    # https://docs.djangoproject.com/en/4.2/ref/contrib/messages/
    messages.info(request, "Delete-account request received.")

    user = request.user
    # only proceed if the user is authenticated
    if user.is_authenticated:
        try:
            # try to get the author and delete it
            author = Author.objects.get(user=user)
            author.delete()
            messages.success(request, "The user has been deleted")  
            return Response(status=200)
        except Author.DoesNotExist:
            # if the user does not exist, respond with a 404
            messages.error(request, "User does not exist")    
            return Response(status=404)
        except Exception as e: 
            # if a general exception occurs, respond with a 500
            return Response(status=500)

    else:
        return Response(status=401)


@api_view(['GET'])
def getNodeHosts(request):
    '''
    PRIVATE: Get node host names
    '''
    user = request.user
    if user.is_authenticated:
        # get all node objects
        nodes = Node.objects.all()
        data = []
        for node in nodes:
            # only append node info if the node hostname is in one of the following
            if node.hostname not in ['super-coding-team', 'req1', 'req2']:
                data.append([node.hostname, node.username, node.password])
        
        return Response(data, status=200)
    return Response(status=401)


#api/delete-inbox-item/<str:author_id>/posts/<str:post_id>/
@api_view(['DELETE'])
def deleteInboxPost(request, author_id, post_id):
    '''
    PRIVATE: Delete a specific inbox post
    '''
    user = request.user
    if user.is_authenticated:
        # get the author and its serializer
        author = Author.objects.get(id=author_id)
        author_serializer = AuthorSerializer(author, context={'request': request})
        # get a dictionary representation of the author data
        serialized_author = author_serializer.data
        # get inbox items from the author
        items = Inbox.objects.filter(author_id=serialized_author['id'])

        # url holds the built url
        url = request.build_absolute_uri()
        # parts holds a list of the individual components of the url
        parts = url.split('/')
        # url now holds a custom url using the information from `parts` and `author_id`
        url = f"{parts[0]}//{parts[2]}/authors/{author_id}/posts/{post_id}"

        
        for item in items:
            # if the item is a post and matches the url matches the pattern of the item endpoint, then delete the item
            if item.type == 'post' and re.match(rf"^{parts[0]}//{parts[2]}/authors/.*/posts/{post_id}$", item.endpoint):
                item.delete()
        
        return Response(status=200)
    return Response(status=401)


@api_view(['PUT'])
def updateUser(request, id):
    user = request.user
    # only proceed if the user is authenticated and the id matches up with the provided id
    if user.is_authenticated and user.id == id:
        # get the user and author objects
        user_object = User.objects.get(id=id)
        author = Author.objects.get(user=user_object)

        # get the profile pic, username, bio, and github information from the request
        request_profileImage = request.data["profileImage"]
        request_username = request.data["username"]
        request_bio = request.data["bio"]
        request_github = request.data["github"]

        # update the users information as necessary
        if request_profileImage.startswith("https://imgur.com/") or request_profileImage.startswith("https://i.imgur.com/"):
            author.profileImage = request_profileImage

        if request_username:
            user_object.username = request_username
        
        if request_bio:
            author.bio = request_bio
        
        if request_github:
            author.github = request_github

        user_object.save()
        author.save()

        return Response(status=200)
    else:
        return Response(status=401)


# outwards facing API endpoints
@api_view(['GET'])
#get list of authors with pagination
#/authors/
def getAuthors(request):
    # authenticate the user
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
      
        # get the page number and page size from the request
        # if they are not set, default those values to 1 and 50 respectfully
        pageNum = request.GET.get('page', 1)
        pageSize = request.GET.get('size', 50)

        # get all the authors, ordered by their id
        authors = Author.objects.all().order_by('id')

        # create page with pageSize number of authors
        paginatedAuthors = Paginator(authors, pageSize)

        #paginator crashes if page number is out of range
        try: 
            # get the pageNum page of authors
            page = paginatedAuthors.page(pageNum)
        except:
            return Response(status=404)

        # create an author serializer of the page of authors
        author_serializer = AuthorSerializer(page, many=True, context={'request': request})
        
        # create a date dictionary where items holds a dictionary of authors on the page we calculated
        data = {
            "type": "authors",
            "items": author_serializer.data
        }

        return Response(data, status=200)

    return result


#/authors/{AUTHOR_ID}/
@api_view(['GET', 'POST'])
def authorReqHandler(request, author_id):
    # authenticate the users request
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        #redirect tot the getAuthor function
        if request.method == 'GET': 
            return getAuthor(request, author_id)

        if result == 'self':
            # redirect to the update author function only if 
            # the authentication returns self
            if request.method == 'POST':
                return updateAuthor(request, author_id)
            
        # if the method is post and if the result is other, return a 405
        return Response(status=405)
    return result


# get a single author by id
def getAuthor(request, author_id):
    if author_id == None:
        return Response(status=400)
    
    # get author from given author id
    author = Author.objects.get(id=author_id)

    # if there is no author associated with the id, return 404
    if author == None:
        return Response(status=404)
    # create a serializer of the author
    author_serializer = AuthorSerializer(author, context={'request': request})
    # create a dictionary of the author object
    serialized_author = author_serializer.data
    return Response(serialized_author, status=200)


# update an author by id
def updateAuthor(request, author_id):  
    if author_id == None:
        return Response(status=400)

    # Get author object from id
    author = Author.objects.get(id=author_id)

    if author == None:
        return Response(status=404)
    
    #check authorization
    if author.user != request.user or not request.user.is_authenticated:
        return Response(status=401)

    author_serializer = AuthorSerializer(author, data=request.data, partial=True)

    if author_serializer.is_valid():
        author_serializer.save()
        return Response(status=200)
    else:
        return Response(status=400)


#/authors/{AUTHOR_ID}/followers
@api_view(['GET'])
def getFollowers(request, author_id):
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        #TODO this currently returns all followers rather than just the ones that are accepted
        #TODO this fails to return any followers where author_data is null, 
        # but a POST to authors/<str:author_id>/followers/requests has no way of writing author_data
        if author_id == None:
            return Response(status=400)
        
        # url holds a built url
        url = request.build_absolute_uri()
        # shorten the url by 10 characters
        url = url[:len(url)-10]

        follower_authors = []
        # get a list of followers from the url
        followers = Follower.objects.filter(followee_endpoint=url)
        for f in followers:
            follower_authors.append(f.follower_data)

        returnDict = {"type": "followers", "items": follower_authors}

        return Response(returnDict)

    return result

@api_view(['GET', 'POST'])
def getFollowRequests(request, author_id):
    # authenticate the users request
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self']:
        # build url and shorten it by 19 characters
        url = request.build_absolute_uri()
        url = url[:len(url)-19]

        if request.method == 'GET':
            followRequests = Follower.objects.filter(followee_endpoint=url, accepted=False)

            data = []
            # append data with follower data from the built url
            for fr in followRequests:
                data.append(fr.follower_data)

            return Response(data, status=200)

        elif request.method == 'POST':
            status = request.data['status']

            if request.data['mode'] == 'update-direct':
                follower_endpoint = request.data['follower_endpoint']
                # get follow request from follower and followee endpoint
                fr = Follower.objects.filter(followee_endpoint=url, follower_endpoint=follower_endpoint).first()

                if fr == None:
                    return Response(status=404)
                
                # friend request has been accepted
                if status == 'accept':
                    fr.accepted = True
                    # get the first follower object with the following criteria
                    frReverse = Follower.objects.filter(followee_endpoint=follower_endpoint, follower_endpoint=url).first()
                    # if there is a mutual following, then friendship is true
                    if frReverse != None and frReverse.accepted == True:
                        frReverse.friendship = True
                        fr.friendship = True
                        frReverse.save()

                    fr.save()

                    return Response(status=200)

                elif status == 'dismiss':
                    fr.delete()

                    return Response(status=204)

                elif status == 'none':
                    return Response(status=200)

            elif request.data['mode'] == 'update-indirect':
                followee_endpoint = request.data['follower_endpoint']
                # followee is obtained from the endpoint while follower is obtained from the url
                fr = Follower.objects.filter(followee_endpoint=followee_endpoint, follower_endpoint=url).first()

                if fr == None:
                    return Response(status=404)

                if status == 'accept':
                    fr.accepted = True
                    # followee is obtained from the url while follower is obtained from the endpoint
                    frReverse = Follower.objects.filter(followee_endpoint=url, follower_endpoint=followee_endpoint).first()
                    if frReverse != None and frReverse.accepted == True:
                        frReverse.friendship = True
                        fr.friendship = True
                        frReverse.save()

                    fr.save()

                    return Response(status=200)

                elif status == 'dismiss':
                    fr.delete()

                    return Response(status=204)

                elif status == 'none':
                    return Response(status=200)
            return Response('Unaccepted status', status=400)
        return Response(status=405)
    return result

#/authors/{AUTHOR_ID}/following
@api_view(['GET'])
def getFollowing(request, author_id):
    # authenticate user request
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result == 'self':
        # build the url and shorten it by 10 characters
        url = request.build_absolute_uri()
        url = url[:len(url)-10] 
        # get the following object where the follower_endpoint is obtained via the url
        following = Follower.objects.filter(follower_endpoint=url)
        data = {}
        for i, follow in enumerate(following):
            # init the default status as 'follow' and change it according to the 
            # below switch case
            status = 'follow'
            if follow.friendship == True:
                status = 'friends'
            elif follow.accepted == True:
                status = 'following'
            elif follow.accepted == False and follow.dismissed == False:
                status = 'requested'
            # add the status and followee into data
            data[i] = {'status': status, 'followee': follow.followee_endpoint}
        return Response(data, status=200)
    return Response(status=401)


#/authors/{AUTHOR_ID}/friends
@api_view(['GET'])
def getFriends(request, author_id):
    # authenticate the users request
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result == 'self':
        # build the url and shorten it by 8 characters
        url = request.build_absolute_uri()
        url = url[:len(url)-8] 

        data = []
        # get the following object based on the url
        following = Follower.objects.filter(follower_endpoint=url)
        for follower in following:
            if follower.friendship == True:
                # if friends with follower, add the endpoint to the list
                data.append(follower.followee_endpoint)

        return Response(data, status=200)
    return Response(status=401)


#/authors/{AUTHOR_ID}/followers/{FOREIGN_AUTHOR_ID}/
@api_view(['GET', 'PUT', 'DELETE'])
def followerReqHandler(request, author_id, foreign_author_id):
    # authenticate the user's request
    result = getAuthed(request.META.get('HTTP_AUTHORIZATION', ''))
    if result in ['self', 'other']:
        if foreign_author_id == None or author_id == None:
            return Response(status=400)
        
        # get followee from the author id
        followee = Author.objects.get(id=author_id)

        if followee == None:
            return Response(status=404)
        
        if request.method == 'GET':
            # build the url, split it via '/', and then build a custom url
            url = request.build_absolute_uri()
            parts = url.split("/")
            url = f"{parts[0]}//{parts[2]}/{parts[3]}/"

            # get the following object from the url/author_id endpoint
            following = Follower.objects.filter(followee_endpoint=url+author_id)
            for f in following:
                # return true when a f that is a follower is met
                if f"/{foreign_author_id}" in f.follower_endpoint and f.accepted == True:
                    return Response({'is_follower': True}, status=200)
            return Response({'is_follower': False}, status=200)
        
        # no follower found
        
        if result == 'self':
            if request.method == 'PUT':
                # create a new follower object
                follow = Follower(
                    follower_data = json.dumps(request.data['follower_data']),
                    follower_endpoint = request.data['follower_data']['id'],
                    follower_host = request.data['follower_data']['host'],
                    followee_data = json.dumps(request.data['followee_data']),
                    followee_endpoint = request.data['followee_data']['id'],
                    followee_host = request.data['followee_data']['host'],
                    dismissed = False,
                    accepted = False,
                    friendship = False,
                    created_at = datetime.now(pytz.timezone('America/Edmonton'))
                )

                follow.save()
                
                # create data that sends type, summary, actor, and object 
                data = {
                    "type": 'Follow',
                    'summary': f"{request.data['follower_data']['displayName']} has requested to follow {request.data['followee_data']['displayName']}",
                    'actor': request.data['follower_data'],
                    "object": request.data['followee_data']
                }

                return Response(data, status=200)


            elif request.method == 'DELETE':
                # get follower object
                f = Follower.objects.filter(
                    follower_endpoint = request.data['follower_endpoint'],
                    followee_endpoint = request.data['followee_endpoint']
                ).first()
                
                # get the reverse follower object
                fReverse = Follower.objects.filter(
                    follower_endpoint = request.data['followee_endpoint'],
                    followee_endpoint = request.data['follower_endpoint']
                ).first()

                # if the reverse does not exist, set friendship to false
                if fReverse != None:
                    fReverse.friendship = False
                    fReverse.save()
                
                # if follower does not exist, delete it
                if f != None:
                    f.delete()

                return Response(status=200)
            
            # if the request is not GET, POST, or DELETE, return 405
        return Response(status=405)
    return result
            

#TODO Friend / follow request (The spec is unclear on the path for this, so leaving it for later)
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def postReqHandler(request, author_id, post_id):
    # authenticate the users request
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        if post_id == None:
            return Response(status=400)
        
        # route to getPost
        if request.method == 'GET': 
            return getPost(request, post_id)
        
        if result == 'self':
            # route to updatePost
            if request.method == 'POST':
                return updatePost(request, post_id)

            # route to creating a post
            elif request.method == 'PUT':
                return createSpecificPost(request, author_id, post_id)
            
            # route to deleting a post
            elif request.method == 'DELETE':
                return deletePost(request, post_id)

            else:
                return Response(status=405)
        return Response(status=405)
    return result


def getPost(request, post_id):
    # get first post with id = post_id
    found_post = Post.objects.filter(id=post_id).first()
    if found_post == None:
        return Response(status=404)
    post_serializer = PostSerializer(found_post, context={'request': request})
    # respond with dictionary of post data
    return Response(post_serializer.data)


def updatePost(request, post_id):
    # get post with id = post_id
    post = Post.objects.get(id=post_id)
    if post is None:
        return Response(status=404)
    
    #check authorization
    if not request.user.is_authenticated:
        return Response(status=401)

    try:
        # update the post's information with info obtained from the request
        post.title = request.data.get('title', post.title)
        post.description = request.data.get('description', post.description)
        post.categories = request.data.get('categories', post.categories)
        post.content = request.data.get('content', post.content)
        post.save()

        return Response(status=200)
    except Exception as e:
        return Response(status=400)


def deletePost(request, post_id):
    # get post with id = post_id
    found_post = Post.objects.get(id=post_id)
    if found_post == None:
        return Response(status=404)
    # delete the post
    found_post.delete()
    return Response(status=200)


def createSpecificPost(request, author_id, post_id):
    # get author with id = author_id
    author = Author.objects.get(id=author_id)
    if author == None:
        return Response(status=404)
    
    #check authorization
    if author.user != request.user or not request.user.is_authenticated:
        return Response(status=401)


    # check if post id is in use
    if Post.objects.filter(id=post_id).exists():
        return Response(status=409) #409 = conflict

    #slot in id
    request.data['id'] = post_id

    #create post with given id
    post_serializer = PostSerializer(data=request.data, context={'request': request})

    if post_serializer.is_valid():
        post_serializer.save()
        return Response(status=200)
    else:
        return Response(status=400)
    

#not a great name, but it follows the spec
@api_view(['GET', 'POST'])
def postCreationReqHandler(request, author_id):
    # authenticate the users request
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        # route to getAuthorPosts
        if request.method == 'GET':
            return getAuthorPosts(request, author_id)

        if result == 'self':
            # route to createPost only if result returned self
            if request.method == 'POST':
                return createPost(request, author_id)
        return Response(status=405)
    return result
    

#like create specific post, but without the post_id
def createPost(request, author_id):
    # get first author with id=author_id
    author = Author.objects.filter(id=author_id).first()
    if author == None:
        return Response(status=404)

    author_serializer = AuthorSerializer(author, context={'request': request})
    # get dict object of author serializer 
    serialized_author = author_serializer.data
    
    #check authorization
    if author.user != request.user or not request.user.is_authenticated:
        return Response(status=401)
    
    # specify the default origin
    default_origin = f'http://{request.get_host()}/author/{author_id}'
    #try:

    source = request.data.get('source')
    # if no source
    if source == '' or source == None:
        # get the post information from the request
        title = request.data.get('title')
        description = request.data.get('description')
        categories = request.data.get('categories', '')
        content = request.data.get('content')
        contentType = request.data.get('contentType', 'text/plain')
        publicity = request.data.get('publicity')
        origin = request.data.get('origin', default_origin).rstrip('/')
        image = request.data.get('image')

        if image:
            contentType = content.split(",")[0].split(":")[1]

        # assume unlisted false
        unlisted = False
        # publicity 0 is public
        # publicity 1 is private
        if publicity == 'public':
            publicity = 0
        elif publicity == 'friends':
            publicity = 1
        elif publicity == 'unlisted':
            publicity = 0
            unlisted = True
        else:
            publicity = -1 #Unknown publicity
        
        # create a new post based on the publicity
        post = Post(
                author_data=json.dumps(serialized_author),
                author_endpoint=serialized_author['id'].rstrip('/'),
                title=title,
                description=description,
                categories=categories,
                contentType=contentType,
                content=content,
                origin=origin,
                publicity=publicity,
                unlisted=unlisted,
                created_at=datetime.now(pytz.timezone('America/Edmonton'))
            )

        post.save()
        
        # set the origin of the post
        post.origin = post.origin + f'/posts/{post.id}'

        post.save()

        post_serialized = PostSerializer(post, context={'request': request})

        data = json.dumps(post_serialized.data)
        # return a json object of the post data
        return Response(data, status=201)
    
    # if source specified
    else:
        # get id and post from request
        id = request.data.get('post_id')

        post = request.data['post']

        # set publicity to 1 (private) if it is friends only, otherwise 0 (public)
        publicity = 0
        if post['visibility'] == 'FRIENDS':
            publicity = 1

        # create a new post
        new_post = Post(
            author_data=json.dumps(serialized_author),
            author_endpoint=post['author']['id'], 
            title=post['title'],
            description=post['description'],
            categories=post['categories'],
            contentType=post['contentType'],
            content=post['content'],
            source=source.rstrip('/'),
            origin=post['origin'].rstrip('/'),
            publicity=publicity,
            unlisted=post['unlisted'],
            created_at=post['published']
        )

        new_post.save()
        
        # add in the post's source
        source += f"/posts/{new_post.id}"
        new_post.source = source

        new_post.save()

        post_serialized = PostSerializer(new_post, context={'request': request})

        data = json.dumps(post_serialized.data)
        # return a json form of the post data
        return Response(data, status=201)
    #except:
    #    return Response(status=400)
    
#/authors/{AUTHOR_ID}/posts
def getAuthorPosts(request, author_id):
    # get pageNUm and pageSize from the request, 
    # default to 1 and 50 respectfully
    pageNum = request.GET.get('page', 1)
    pageSize = request.GET.get('size', 50)

    if author_id == None:
        return Response(status=400)
    
    # build the url and shorten it by 6 characters
    url = request.build_absolute_uri()
    url = url[:len(url)-6]

    # get all the posts, sorted by creation date
    posts = Post.objects.filter(author_endpoint=url).order_by('created_at')

    # get pageSize number of authors on a page
    paginatedPosts = Paginator(posts, pageSize)

    #paginator crashes if page number is out of range
    try: 
        # get pageNum page
        page = paginatedPosts.page(pageNum)
    except:
        return Response(status=404)

    # create a page of posts as a serializer 
    post_serializer = PostSerializer(page, many=True, context={'request': request})

    serialized_posts = post_serializer.data
    # return the number of posts and the posts themselves 
    return Response({'count': len(serialized_posts), 'items': serialized_posts})


#/authors/{AUTHOR_ID}/posts/{POST_ID}/comments/
@api_view(['GET', 'POST'])
def commentReqHandler(request, author_id, post_id):
    # authenticate the user
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        if post_id == None:
            return Response(status=400)
        
        # route to getComments
        if request.method == 'GET': 
            return getComments(request, post_id)
        
        if result == 'self':
            # route to createComment
            if request.method == 'POST':
                return createComment(request, author_id, post_id)

        return Response(status=405)
    return result
    

def getComments(request, post_id):
    # get first post where id = post_id
    found_post = Post.objects.filter(id=post_id).first()
    if found_post == None:
        return Response(status=404)
    
    # build the post endpoint url from the url generated by the reverse() function. 
    post_endpoint = request.build_absolute_uri(reverse('postReqHandler', args=[found_post.author_endpoint.split('/')[-1], found_post.id]))

    # get comments where the post endpoint = the one we created above, ordered by creation date
    comments = Comment.objects.filter(post_endpoint=post_endpoint).order_by('created_at')
    
    comment_serializer = CommentSerializer(comments, many=True, context={'request': request})
    # create a dict object of the comments on the post
    serialized_comments = comment_serializer.data
    return Response(serialized_comments)


def createComment(request, author_id, post_id):
    # get author where id = author_id
    author = Author.objects.get(id=author_id)
    if author == None:
        return Response(status=404)
    
    # get the first post where post=post_id
    found_post = Post.objects.filter(id=post_id).first()
    if found_post == None:
        return Response(status=404)
    #slot in post ID
    # build the url and shorten it by 9 characters
    url = request.build_absolute_uri()
    url = url[:len(url)-9]
    
    # create a comment based on the url
    comment = Comment(
        author_data=json.dumps(request.data['author']),
        post_endpoint=url,
        content=request.data['comment'],
        created_at=datetime.now(pytz.timezone('America/Edmonton'))
    )

    comment.save()

    data = CommentSerializer(comment, context={'request': request}).data
    # return dict of the comment
    return Response(data, status=200)

@api_view(['POST'])
def createCommentData(request):
    # authenticate the user's request
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result == 'self':
        # create a comment object using information from the request
        comment = Comment(
            author_data=json.dumps(request.data['author']),
            post_endpoint=request.data['post'],
            content=request.data['comment'],
            created_at=datetime.now(pytz.timezone('America/Edmonton'))
        )

        # create a comment serializer 
        data = CommentSerializer(comment, context={'request': request}).data
        
        
        if request.data['destination'] == 'there':
            # change the value of data['id'] to the post data + 'comments/'
            data['id'] = request.data['post'] + 'comments/' 

        return Response(data, status=200)
    return Response(status=401)
    

# /authors/{AUTHOR_ID}/inbox/
@api_view(['POST', 'GET', 'DELETE'])
def inboxReqHandler(request, author_id):
    '''
    POST: Public
        The request data should be the serialized/stringified json of the object you are sending
        Ex. if the object is type post then the request data is the post data following the specs in string form
    GET: Private
    DELETE: Private
    '''
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:

        # route to inboxPostHandler
        if request.method == 'POST':
            return inboxPOSTHandler(request, author_id)

        if result == 'self':
            if request.method == 'GET':
                # get the page num and size from the request,
                # defaulted to 1 and 50 respectfully
                pageNum = request.GET.get('page', 1)
                pageSize = request.GET.get('size', 50)
                interval = request.GET.get('interval', 'no')

                
                # get the first author object where id = author_id
                author = Author.objects.filter(id=author_id).first()

                if author == None:
                    return Response(status=404)
                
                # if user is not authenticated or the user is not the author, respond with a 401
                if not request.user.is_authenticated or request.user != author.user:
                    return Response(status=401)
                
                # create a serializer for the author 
                author_serializer = AuthorSerializer(author, context={'request': request})
                # store the id from the dict 
                author_url_id = author_serializer.data['id']

                if interval == 'yes':
                    # get the inbox items with the specified id that are less than 2 seconds old, ordered by creation date
                    newTime = datetime.now(pytz.timezone('America/Edmonton')) - timedelta(seconds=2)
                    inbox_items = Inbox.objects.filter(author_id=author_url_id, created_at__gt=newTime).order_by('-created_at')
                else:
                    # get the inbox items with the specified id, ordered by creation date
                    inbox_items = Inbox.objects.filter(author_id=author_url_id).order_by('-created_at')

                # create pages of items with the number of items on each page equal to pageSize
                paginatedItems = Paginator(inbox_items, pageSize)

                #paginator crashes if page number is out of range
                try: 
                    # get pageNum page of items
                    page = paginatedItems.page(pageNum)
                except:
                    return Response(status=404)

                # create a serializer of the page of items
                inbox_serializer = InboxSerializer(page, many=True, context={'request': request})
                # create a dict of the items info
                serialized_inbox_items = inbox_serializer.data
                # create a data dict containing type, author, and items
                serialized_inbox = {'type': 'inbox', "author": author_url_id, 'items': serialized_inbox_items}
                return Response(serialized_inbox)

            elif request.method == 'DELETE':
                # get first author where id = post_id
                author = Author.objects.filter(id=author_id).first()
                if author == None:
                    return Response(status=404)
                
                # create serializer and dict of the author
                author_serializer = AuthorSerializer(author, context={'request': request})
                serialized_author = author_serializer.data

                # get the items where the author id = the id from the serializer, ordered by creation date 
                inbox_items = Inbox.objects.filter(author_id=serialized_author.get('id')).order_by('created_at')
                # delete these items from the inbox
                inbox_items.delete()
                return Response(status=200)

        return Response(status=405)
    return result
    

def inboxPOSTHandler(request, recieving_author_id):
    # get data from the request
    data = request.data
    
    if data['type'].lower() == 'like':
        # if the data type is like, create a like object, 
        # using data obtained from the request
        like = Like(
            author_endpoint = data['author']['id'],
            author_data = json.dumps(data['author']),
            summary = data['summary']
        )

        if data['object'].split('/')[-2] == 'posts':
            # if the data object is posts, add the object to the post endpoint
            like.post_endpoint = data['object']
        else:
            # if the data object is comments, add the object to the comment endpoint
            like.comment_endpoint = data['object']

        like.save()

        return Response(status=200)
    

    elif data['type'].lower() == 'post':
        # get author objects where id is requested id
        author = Author.objects.get(id=recieving_author_id)
        author_serializer = AuthorSerializer(author, context={'request': request})
        # create a dict object of the authors data
        serialized_author = author_serializer.data

        # create an inbox object of posts by the author
        Inbox.objects.create(
            author_id=serialized_author['id'], 
            endpoint=data['id'],
            type=data['type']
        )

        return Response(status=200)
    
    elif data['type'].lower() == 'comment':
        # get the id from the data and split it via '/'
        parts = data['id'].split('/')
        # create a custom link using parta
        post_endpoint = f"{parts[0]}//{parts[2]}/{parts[3]}/{parts[4]}/{parts[5]}/{parts[6]}"
        
        # create a comment object 
        comment = Comment(
            author_data = json.dumps(data['author']),
            post_endpoint = post_endpoint,
            content = data['comment'],
            created_at = datetime.now(pytz.timezone('America/Edmonton'))
        )

        comment.save()

        return Response(status=200)

    elif data['type'].lower() == 'follow':
        # create a follow object based on values obtained from request
        follow = Follower(
            follower_endpoint = data['actor']['id'],
            follower_host = data['actor']['host'],
            follower_data = json.dumps(data['actor']),
            followee_endpoint = data['object']['id'],
            followee_host = data['object']['host'],
            followee_data = json.dumps(data['object']),
            dismissed = False,
            accepted = False,
            friendship = False,
            created_at = datetime.now(pytz.timezone('America/Edmonton'))
        )

        follow.save()

        return Response(status=200)

    else:
        return Response(status=400)


#/authors/{AUTHOR_ID}/posts/{POST_ID}/likes
@api_view(['GET', 'POST'])
def getPostLikes(request, author_id, post_id):
    # authenticate the users request
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        if request.method == 'GET':
            if post_id == None:
                return Response(status=400)
            
            # build the url and split it via '/'
            url = request.build_absolute_uri()
            parts = url.split('/')
            # create a start and end urls
            start = f"{parts[0]}//{parts[2]}"
            end = f"{parts[5]}/{parts[6]}"

            # get all like objects where the post endpoint begins with 'start' and ends with 'end'
            likes = Like.objects.filter(Q(post_endpoint__contains=start) & Q(post_endpoint__contains=end)).order_by('created_at')
            
            like_serializer = LikeSerializer(likes, many=True, context={'request': request})
            # create a dict structure of the serializer
            serialized_likes = like_serializer.data
            return Response(serialized_likes)

        if result == 'self':
            if request.method == 'POST':
                user = request.user
                # authenticate user
                if user.is_authenticated:
                    # build the url and shorten it by 6 characters
                    url = request.build_absolute_uri()
                    parts = url.split('/')
                    url = url[:len(url)-6]
                    # create a like object using data obtained from the request
                    like = Like(
                        author_endpoint=request.data['author_endpoint'],
                        author_data=json.dumps(request.data['author_data']),
                        post_endpoint=request.data['object'],
                        summary=f"{user.username} like your post", 
                        created_at=datetime.now(pytz.timezone('America/Edmonton'))
                    )
                    
                    if (request.data['destination'] == 'here'):
                        like.save()

                    # create a serializer and then a data dict 
                    like_serializer = LikeSerializer(like, context={'request': request})
                    data = like_serializer.data

                    return Response(data, status=201)
                return Response(status=401) 


            # THIS IS NO LONGER USED
            # USE IF WE DECIDE TO UNLIKE POSTS AGAIN
            # elif request.method == 'DELETE':
            #     user = request.user
            #     if user.is_authenticated:
            #         url = request.build_absolute_uri()
            #         url = url[:len(url)-6]

            #         author = Author.objects.get(id=author_id)

            #         like = Like.objects.get(author=author, post_endpoint=url)

            #         like.delete()

            #         return Response(status=200)
            #     return Response(status=401) 
            
        return Response(status=405)
    return result


#/authors/{AUTHOR_ID}/posts/{POST_ID}/comments/{COMMENT_ID}/likes/   
@api_view(['GET', 'POST'])
def getCommentLikes(request, author_id, post_id, comment_id):
    # authenticate the users request
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        if request.method == 'GET':
            # build the url, split it, create a start and end of the url
            url = request.build_absolute_uri()
            parts = url.split('/')
            start = f"{parts[0]}//{parts[2]}"
            end = f"{parts[7]}/{parts[8]}"

            # get all likes where the comment endpoint starts and ends with 'start' and 'end' respectfully
            likes = Like.objects.filter(Q(comment_endpoint__contains=start) & Q(comment_endpoint__contains=end)).order_by('created_at')
            like_serializer = LikeSerializer(likes, many=True, context={'request': request})

            # get a dict of the likes
            serialized_likes = like_serializer.data
            return Response(serialized_likes, status=200)

        if result == 'self':
            if request.method == 'POST':
                # authenticate user
                user = request.user
                if user.is_authenticated:
                    # create a like object using the data from the request
                    like = Like(
                        author_endpoint=request.data['author_endpoint'],
                        author_data=json.dumps(request.data['author_data']),
                        comment_endpoint=request.data['object'],
                        summary=f"{user.username} like your post", 
                        created_at=datetime.now(pytz.timezone('America/Edmonton'))
                    )

                    if (request.data['destination'] == 'here'):
                        like.save()

                    like_serializer = LikeSerializer(like, context={'request': request})
                    # create a data dict of the like object
                    data = like_serializer.data

                    return Response(data, status=201)
                return Response(status=401) 
        return Response(status=405)
    return result


#/authors/{AUTHOR_ID}/liked
@api_view(['GET'])
def getAuthorLiked(request, author_id):
    # authenticate the users request
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        # ensure only get requests make it through
        if request.method != 'GET':
            return Response(status=405)

        if author_id == None:
            return Response(status=400)
        
        # get first author object where id = author_id
        found_author = Author.objects.filter(id=author_id).first()

        # if there is no such author, return 404
        if found_author == None:
            return Response(status=404)
        
        # build the url, get all like objects based on this url, ordered by creation date
        author_url = request.build_absolute_uri(reverse('authorReqHandler', args=[found_author.id]))
        likes = Like.objects.filter(author_endpoint=author_url).order_by('created_at')
        # create a serializer and return the data in the form of a dict
        like_serializer = LikeSerializer(likes, many=True, context={'request': request})
        serialized_likes = like_serializer.data
        return Response(serialized_likes)
    return result