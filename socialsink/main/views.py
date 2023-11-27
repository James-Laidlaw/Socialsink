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
    author = Author.objects.get(user=request.user)

    author_serializer = AuthorSerializer(author, context={'request': request})
    serialized_author = author_serializer.data

    return render(request=request,
                  template_name='main/home.html',
                  context={'user': request.user,
                           'author': author,
                           'author_endpoint': serialized_author['id']})


def login(request):
    return render(request=request,
                  template_name='main/login.html',
            
                  context={})


def register(request):
    return render(request=request,
                  template_name='main/register.html',
                  context={})


def displayPost(request, id):
    user = request.user
    if user.is_authenticated:

        author = Author.objects.get(user=user)
        
        post = Post.objects.filter(id=id).first()
        if post == None:
            return redirect('/')

        permission = False
        following = author.following.all()
        for f in following:
            if f.followee == post.author and f.friendship == True:
                permission = True

        if post.publicity == 1 and not permission:
            return redirect('/')

        liked = author.likes.filter(post=post)
        if len(liked) == 0:
            liked = 0
        else:
            liked = 1

        post_serializer = PostSerializer(post, context={'request': request})

        return render(request=request,
                      template_name='main/post.html',
                      context={'post': json.dumps(post_serializer.data | {'like-count': len(post.likes.all()), 'liked': liked}),
                               'author': author})
        
    else:
        return redirect('/login/')


def getAuthed(auth_header):
    if not len(auth_header):
        return Response({"Unauthorized."}, status=401)
    token_type, _, credentials = auth_header.partition(' ')
    try:
        username, password = base64.b64decode(credentials).decode().split(':')
        node = Node.objects.filter(username=username, password=password).first()
        if node == None:
            return Response("Error decoding Authorization header", status=401)

        if node.username == 'socialsink':
            return 'self'
        else:
            return 'other'

    except:
        return Response("Error decoding Authorization header", status=400)


@api_view(['PUT'])
def createAccount(request):
    username = request.data['username']
    email = request.data['email']
    password = request.data['password']

    ss = ServerSettings.objects.first()

    try:    
        user = User.objects.create_user(username=username, email=email, password=password)
        if ss.auto_permit_users == True:
            author = Author(user=user, created_at=datetime.now(pytz.timezone('America/Edmonton')))
        else:
            author = Author(user=user, created_at=datetime.now(pytz.timezone('America/Edmonton')), is_permitted=False)
        author.save()
        user.author = author
        user.save()

        if ss.auto_permit_users == True:
            auth_login(request, user)
        else:
            return Response(status=301)
        return Response(status=201)
        
    except:
        return Response(status=500)


@api_view(['POST'])
def loginRequest(request):
    username = request.data['username']
    password = request.data['password']

    user = authenticate(username=username, password=password)

    author = Author.objects.get(user=user)
    if author.is_permitted:
        if user != None:
            auth_login(request, user)
            return Response(status=201)
    else:
        return Response(status=301)

    return Response(status=401)

@api_view(['GET'])
def logoutRequest(request):
    auth_logout(request)
    return Response(status=200)


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


@api_view(['GET'])
def getNodeHosts(request):
    '''
    PRIVATE: Get node host names
    '''
    user = request.user
    if user.is_authenticated:
        nodes = Node.objects.all()
        data = []
        for node in nodes:
            if node.hostname not in ['super-coding-team', 'req1', 'req2']:
                data.append([node.hostname, node.username, node.password])
        
        return Response(data, status=200)
    return Response(status=401)


@api_view(['DELETE'])
def deleteInboxPost(request, author_id, post_id):
    '''
    PRIVATE: Delete a specific inbox post
    '''
    user = request.user
    if user.is_authenticated:
        author = Author.objects.get(id=author_id)
        items = Inbox.objects.filter(author=author)

        url = request.build_absolute_uri()
        parts = url.split('/')
        url = f"{parts[0]}//{parts[2]}/authors/{author_id}/posts/{post_id}/"

        for item in items:
            if item.type == 'post' and re.match(rf"^{parts[0]}//{parts[2]}/authors/.*/posts/{post_id}/$", item.endpoint):
                item.delete()
        
        return Response(status=200)
    return Response(status=401)


@api_view(['PUT'])
def updateUser(request, id):
    user = request.user
    if user.is_authenticated and user.id == id:
        
        user_object = User.objects.get(id=id)
        author = Author.objects.get(user=user_object)

        request_profileImage = request.data["profileImage"]
        request_username = request.data["username"]
        request_bio = request.data["bio"]
        request_github = request.data["github"]

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
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
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

        data = {
            "type": "authors",
            "items": author_serializer.data
        }

        return Response(data, status=200)

    return result


#/authors/{AUTHOR_ID}/
@api_view(['GET', 'POST'])
def authorReqHandler(request, author_id):
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        if request.method == 'GET': 
            print("service: Get author request received")
            return getAuthor(request, author_id)

        if result == 'self':
            if request.method == 'POST':
                print("service: Update author request received")
                return updateAuthor(request, author_id)
        return Response(status=405)
    return result


# get a single author by id
def getAuthor(request, author_id):
    if author_id == None:
        return Response(status=400)
    
    author = Author.objects.get(id=author_id)

    if author == None:
        return Response(status=404)
    author_serializer = AuthorSerializer(author, context={'request': request})

    serialized_author = author_serializer.data
    return Response(serialized_author, status=200)


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
        return Response(status=200)
    else:
        return Response(status=400)


#/authors/{AUTHOR_ID}/followers/
@api_view(['GET'])
def getFollowers(request, author_id):
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        print("service: Get followers request received")
        if author_id == None:
            return Response(status=400)

        url = request.build_absolute_uri()
        url = url[:len(url)-10]
        
        follower_authors = []
        followers = Follower.objects.filter(followee_endpoint=url)
        for f in followers:
            follower_authors.append(f.followee_data)

        returnDict = {"type": "followers", "items": follower_authors}

        return Response(returnDict)

    return result

@api_view(['GET', 'POST'])
def getFollowRequests(request, author_id):
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self']:
        url = request.build_absolute_uri()
        url = url[:len(url)-19]

        if request.method == 'GET':
            followRequests = Follower.objects.filter(followee_endpoint=url, accepted=False)

            data = []
            for fr in followRequests:
                data.append(fr.follower_data)

            return Response(data, status=200)

        elif request.method == 'POST':
            status = request.data['status']
            print(status)

            if request.data['mode'] == 'update-direct':
                follower_endpoint = request.data['follower_endpoint']

                print(url)
                print(follower_endpoint)
                
                fr = Follower.objects.filter(followee_endpoint=url, follower_endpoint=follower_endpoint).first()

                if fr == None:
                    return Response(status=404)

                if status == 'accept':
                    fr.accepted = True

                    frReverse = Follower.objects.filter(followee_endpoint=follower_endpoint, follower_endpoint=url).first()
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
                
                fr = Follower.objects.filter(followee_endpoint=followee_endpoint, follower_endpoint=url).first()

                if fr == None:
                    return Response(status=404)

                if status == 'accept':
                    fr.accepted = True

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
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result == 'self':
        url = request.build_absolute_uri()
        url = url[:len(url)-10] 

        following = Follower.objects.filter(follower_endpoint=url)
        data = {}
        for i, follow in enumerate(following):
            status = 'follow'
            if follow.friendship == True:
                status = 'friends'
            elif follow.accepted == True:
                status = 'following'
            elif follow.accepted == False and follow.dismissed == False:
                status = 'requested'
            data[i] = {'status': status, 'followee': follow.followee_endpoint}
        return Response(data, status=200)
    return Response(status=401)


#/authors/{AUTHOR_ID}/friends
@api_view(['GET'])
def getFriends(request, author_id):
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result == 'self':
        url = request.build_absolute_uri()
        url = url[:len(url)-8] 

        data = []
        following = Follower.objects.filter(follower_endpoint=url)
        for follower in following:
            if follower.friendship == True:
                data.append(follower.followee_endpoint)

        return Response(data, status=200)
    return Response(status=401)


#/authors/{AUTHOR_ID}/followers/{FOREIGN_AUTHOR_ID}/
@api_view(['GET', 'PUT', 'DELETE'])
def followerReqHandler(request, author_id, foreign_author_id):
    print("service: Get follower-followee relationship details request received")
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        if foreign_author_id == None or author_id == None:
            return Response(status=400)
        
        followee = Author.objects.get(id=author_id)

        if followee == None:
            return Response(status=404)
        
        if request.method == 'GET':
            url = request.build_absolute_uri()
            parts = url.split("/")
            url = f"{parts[0]}//{parts[2]}/{parts[3]}/"

            print(url)

            following = Follower.objects.filter(followee_endpoint=url+author_id+'/')
            for f in following:
                if f"/{foreign_author_id}/" in f.follower_endpoint and f.accepted == True:
                    return Response(True, status=200)
            return Response(False, status=200)
        
        if result == 'self':
            if request.method == 'PUT':
                print(request.data)
                follower_instance = Follower.objects.filter(
                    follower_endpoint = request.data['follower_data']['id'],
                    followee_endpoint = request.data['followee_data']['id']
                )
                
                if follower_instance == None:
                    return Response(status=409)

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

                data = {
                    "type": 'Follow',
                    'summary': f"{request.data['follower_data']['displayName']} has requested to follow {request.data['followee_data']['displayName']}",
                    'actor': request.data['follower_data'],
                    "object": request.data['followee_data']
                }

                return Response(data, status=200)


            elif request.method == 'DELETE':
                f = Follower.objects.filter(
                    follower_endpoint = request.data['follower_endpoint'],
                    followee_endpoint = request.data['followee_endpoint']
                ).first()

                fReverse = Follower.objects.filter(
                    follower_endpoint = request.data['followee_endpoint'],
                    followee_endpoint = request.data['follower_endpoint']
                ).first()

                if fReverse != None:
                    fReverse.friendship = False
                    fReverse.save()

                if f != None:
                    f.delete()

                return Response(status=200)
            
            # if the request is not GET, POST, or DELETE, return 405
        return Response(status=405)
    return result
            

#TODO Friend / follow request (The spec is unclear on the path for this, so leaving it for later)
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def postReqHandler(request, author_id, post_id):
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        if post_id == None:
            print("service: no post id, returning 400 ***********************************************")
            return Response(status=400)
        
        if request.method == 'GET': 
            print("service: Get post request received")
            return getPost(request, post_id)
        
        if result == 'self':
            if request.method == 'POST':
                print("service: Update post request received")
                return updatePost(request, post_id)

            elif request.method == 'PUT':
                print("service: Create specific post request received")
                return createSpecificPost(request, author_id, post_id)
            
            elif request.method == 'DELETE':
                print("service: Delete post request received")
                return deletePost(request, post_id)

            else:
                return Response(status=405)
        return Response(status=405)
    return result


def getPost(request, post_id):
    found_post = Post.objects.filter(id=post_id).first()
    if found_post == None:
        return Response(status=404)
    post_serializer = PostSerializer(found_post, context={'request': request})
    return Response(post_serializer.data)


def updatePost(request, post_id):
    post = Post.objects.get(id=post_id)
    if post is None:
        return Response(status=404)
    
    #check authorization
    if post.author.user != request.user or not request.user.is_authenticated:
        print("unauthorized, returning 401")
        return Response(status=401)

    try:
        post.title = request.data.get('title', post.title)
        post.description = request.data.get('description', post.description)
        post.categories = request.data.get('categories', post.categories)
        post.content = request.data.get('content', post.content)
        post.save()

        return Response(status=200)
    except Exception as e:
        print(e)
        return Response(status=400)


def deletePost(request, post_id):
    found_post = Post.objects.get(id=post_id)
    if found_post == None:
        return Response(status=404)
    found_post.delete()
    return Response(status=200)


def createSpecificPost(request, author_id, post_id):
    author = Author.objects.get(id=author_id)
    if author == None:
        return Response(status=404)
    
    #check authorization
    if author.user != request.user or not request.user.is_authenticated:
        print("unauthorized, returning 401")
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
    
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        if request.method == 'GET':
            print("service: Get posts request received")
            return getAuthorPosts(request, author_id)

        if result == 'self':
            if request.method == 'POST':
                print("service: Create post request received")
                return createPost(request, author_id)
        return Response(status=405)
    return result
    

#like create specific post, but without the post_id
def createPost(request, author_id):
    author = Author.objects.filter(id=author_id).first()
    if author == None:
        return Response(status=404)
    
    #check authorization
    if author.user != request.user or not request.user.is_authenticated:
        print("unauthorized, returning 401")
        return Response(status=401)
    
    default_origin = f'http://{request.get_host()}/author/{author_id}/'
    #try:

    source = request.data.get('source')
    if source == '' or source == None:
        title = request.data.get('title')
        description = request.data.get('description')
        categories = request.data.get('categories', '')
        content = request.data.get('content')
        contentType = request.data.get('contentType', 'text/plain')
        publicity = request.data.get('publicity')
        origin = request.data.get('origin', default_origin)
        image = request.data.get('image')

        if image:
            contentType = content.split(",")[0].split(":")[1]

        unlisted = False
        if publicity == 'public':
            publicity = 0
        elif publicity == 'friends':
            publicity = 1
        elif publicity == 'unlisted':
            publicity = 0
            unlisted = True
        else:
            publicity = -1 #Unknown publicity

        post = Post(
                author=author,
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

        origin += f'posts/{post.id}'

        post.origin = origin

        post.save()

        post_serialized = PostSerializer(post, context={'request': request})

        data = json.dumps(post_serialized.data)

        return Response(data, status=201)
    else:
        id = request.data.get('post_id')
        
        post = Post.objects.filter(id=id).first()
        if post == None:
            return Response(status=404)

        new_post = Post(
            author=author, 
            title=post.title,
            description=post.description,
            categories=post.categories,
            contentType=post.contentType,
            content=post.content,
            source=source,
            origin=post.origin,
            publicity=post.publicity,
            unlisted=post.unlisted,
            created_at=post.created_at
        )

        new_post.save()

        source += f"posts/{new_post.id}"
        new_post.source = source

        new_post.save()

        post_serialized = PostSerializer(new_post, context={'request': request})

        data = json.dumps(post_serialized.data)

        return Response(data, status=201)
    #except:
    #    return Response(status=400)
    

def getAuthorPosts(request, author_id):
    pageNum = request.GET.get('page', 1)
    pageSize = request.GET.get('size', 50)

    if author_id == None:
        return Response(status=400)
    
    author = Author.objects.get(id=author_id)

    if author == None:
        return Response(status=404)
    

    posts = author.posts.all().order_by('created_at')

    paginatedPosts = Paginator(posts, pageSize)

    #paginator crashes if page number is out of range
    try: 
        page = paginatedPosts.page(pageNum)
    except:
        return Response(status=404)


    post_serializer = PostSerializer(page, many=True, context={'request': request})

    serialized_posts = post_serializer.data
    return Response(serialized_posts)


#/authors/{AUTHOR_ID}/posts/{POST_ID}/comments
@api_view(['GET', 'POST'])
def commentReqHandler(request, author_id, post_id):
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        if post_id == None:
            return Response(status=400)
        
        if request.method == 'GET': 
            print("service: Get comments request received")
            return getComments(request, post_id)
        
        if result == 'self':
            if request.method == 'POST':
                print("service: Create comment request received")
                return createComment(request, author_id, post_id)

        return Response(status=405)
    return result
    

def getComments(request, post_id):
    found_post = Post.objects.filter(id=post_id).first()
    if found_post == None:
        return Response(status=404)
    
    post_endpoint = request.build_absolute_uri(reverse('postReqHandler', args=[found_post.author.id, found_post.id]))
    
    comments = Comment.objects.filter(post_endpoint=post_endpoint).order_by('created_at')
    
    comment_serializer = CommentSerializer(comments, many=True, context={'request': request})

    serialized_comments = comment_serializer.data
    return Response(serialized_comments)


def createComment(request, author_id, post_id):
    author = Author.objects.get(id=author_id)
    if author == None:
        return Response(status=404)
    
    found_post = Post.objects.filter(id=post_id).first()
    if found_post == None:
        return Response(status=404)
    #slot in post ID

    url = request.build_absolute_uri()
    url = url[:len(url)-9]
    
    comment = Comment(
        author_data=json.dumps(request.data['author']),
        post_endpoint=url,
        content=request.data['comment'],
        created_at=datetime.now(pytz.timezone('America/Edmonton'))
    )

    comment.save()

    data = CommentSerializer(comment, context={'request': request}).data

    return Response(data, status=200)
    

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

        if request.method == 'POST':
            print("service: Inbox POST request received")
            return inboxPOSTHandler(request, author_id)

        if result == 'self':
            if request.method == 'GET':
                print("service: Inbox GET request received")
                pageNum = request.GET.get('page', 1)
                pageSize = request.GET.get('size', 50)
                author = Author.objects.filter(id=author_id).first()

                if author == None:
                    return Response(status=404)
                
                if not request.user.is_authenticated or request.user != author.user:
                    return Response(status=401)

                author_serializer = AuthorSerializer(author, context={'request': request})
                author_url_id = author_serializer.data.get('id')

                inbox_items = Inbox.objects.filter(author_id=author_id).order_by('-created_at')

                paginatedItems = Paginator(inbox_items, pageSize)

                #paginator crashes if page number is out of range
                try: 
                    page = paginatedItems.page(pageNum)
                except:
                    return Response(status=404)


                inbox_serializer = InboxSerializer(page, many=True, context={'request': request})
                serialized_inbox_items = inbox_serializer.data
                serialized_inbox = {'type': 'inbox', "author": author_url_id, 'items': serialized_inbox_items}
                return Response(serialized_inbox)

            elif request.method == 'DELETE':
                print("service: Inbox DELETE request received")
                author = Author.objects.filter(id=author_id).first()
                if author == None:
                    return Response(status=404)

                inbox_items = Inbox.objects.filter(author_id=author_id).order_by('created_at')
                inbox_items.delete()
                return Response(status=200)

        return Response(status=405)
    return result
    

def inboxPOSTHandler(request, recieving_author_id):
    data = request.data
    print(data)
    
    if data['type'].lower() == 'like':
        like = Like(
            author_endpoint = data['author']['id'],
            author_data = json.dumps(data['author']),
            summary = data['summary']
        )

        if data['object'].split('/')[-2] == 'post':
            like.post_endpoint = data['object']
        else:
            like.comment_endpoint = data['object']

        like.save()

        return Response(status=200)
    

    elif data['type'].lower() == 'post':
        Inbox.objects.create(
            author_id=recieving_author_id, 
            endpoint=data['id'],
            type=data['type'])

        return Response(status=200)
    
    elif data['type'].lower() == 'comment':
        comment = Comment(
            author_data = json.dumps(data['author']),
            post_endpoint = data['id'],
            content = data['comment'],
            created_at = datetime.now(pytz.timezone('America/Edmonton'))
        )

        comment.save()

        return Response(status=200)

    elif data['type'].lower() == 'follow':
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


#/authors/{AUTHOR_ID}/posts/{POST_ID}/likes/
@api_view(['GET', 'POST'])
def getPostLikes(request, author_id, post_id):
    print("service: Get post likes request received")
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        if request.method == 'GET':
            if post_id == None:
                return Response(status=400)
            
            url = request.build_absolute_uri()
            parts = url.split('/')
            start = f"{parts[0]}//{parts[2]}"
            end = f"{parts[5]}/{parts[6]}/"

            likes = Like.objects.filter(Q(post_endpoint__contains=start) & Q(post_endpoint__contains=end)).order_by('created_at')

            like_serializer = LikeSerializer(likes, many=True, context={'request': request})

            serialized_likes = like_serializer.data
            return Response(serialized_likes)

        if result == 'self':
            if request.method == 'POST':
                user = request.user
                if user.is_authenticated:
                    url = request.build_absolute_uri()
                    parts = url.split('/')
                    url = url[:len(url)-6]

                    like = Like(
                        author_endpoint=request.data['author_endpoint'],
                        author_data=json.dumps(request.data['author_data']),
                        post_endpoint=url,
                        summary=f"{user.username} like your post", 
                        created_at=datetime.now(pytz.timezone('America/Edmonton'))
                    )

                    if (request.data['destination'] == 'here'):
                        like.save()

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


#/authors/{AUTHOR_ID}/posts/{POST_ID}/comments/{COMMENT_ID}/likes    
@api_view(['GET', 'POST'])
def getCommentLikes(request, author_id, post_id, comment_id):
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        print("service: Get comment likes request received")
        if request.method == 'GET':
            url = request.build_absolute_uri()
            parts = url.split('/')
            start = f"{parts[0]}//{parts[2]}"
            end = f"{parts[7]}/{parts[8]}/"

            likes = Like.objects.filter(Q(comment_endpoint__contains=start) & Q(comment_endpoint__contains=end)).order_by('created_at')
            like_serializer = LikeSerializer(likes, many=True, context={'request': request})

            serialized_likes = like_serializer.data
            return Response(serialized_likes, status=200)

        if result == 'self':
            if request.method == 'POST':
                user = request.user
                if user.is_authenticated:
                    url = request.build_absolute_uri()
                    parts = url.split('/')
                    url = url[:len(url)-6]

                    like = Like(
                        author_endpoint=request.data['author_endpoint'],
                        author_data=json.dumps(request.data['author_data']),
                        comment_endpoint=url,
                        summary=f"{user.username} like your post", 
                        created_at=datetime.now(pytz.timezone('America/Edmonton'))
                    )

                    if (request.data['destination'] == 'here'):
                        like.save()

                    like_serializer = LikeSerializer(like, context={'request': request})
                    data = like_serializer.data

                    return Response(data, status=201)
                return Response(status=401) 
        return Response(status=405)
    return result


#/authors/{AUTHOR_ID}/liked
@api_view(['GET'])
def getAuthorLiked(request, author_id):
    result = getAuthed(request.META['HTTP_AUTHORIZATION'])
    if result in ['self', 'other']:
        print("service: Get author liked request received")
        if request.method != 'GET':
            return Response(status=405)

        if author_id == None:
            return Response(status=400)
        
        found_author = Author.objects.filter(id=author_id).first()

        if found_author == None:
            return Response(status=404)
        
        author_url = request.build_absolute_uri(reverse('authorReqHandler', args=[found_author.id]))
        likes = Like.objects.filter(author_endpoint=author_url).order_by('created_at')
        like_serializer = LikeSerializer(likes, many=True, context={'request': request})
        serialized_likes = like_serializer.data
        return Response(serialized_likes)
    return result