from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .models import Author, Post, Like, Follower, ServerSettings, Comment
from .serizlizers import AuthorSerializer, PostSerializer, CommentSerializer, LikeSerializer

from datetime import datetime, timedelta, date, time
import pytz
from django.contrib import messages
from django.urls import reverse


from rest_framework.decorators import api_view
from rest_framework.response import Response

#Image Imports
from django.core.files.base import ContentFile
import base64
from PIL import Image
from io import BytesIO
import json

# Create your views here.
@login_required
def homepage(request):
    author = Author.objects.get(user=request.user)
    return render(request=request,
                  template_name='main/home.html',
                  context={'user': request.user,
                           'author': author})

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
        return Response(status=401)

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

@api_view(['GET'])
def getOldInboxInfo(request):
    user = request.user
    if user.is_authenticated:
        data = {}

        #Get the author id for inbox
        aids = []
        primary_author = Author.objects.get(user=user)
        aids.append(primary_author.id)
        #Get the list of authors
        authors = Author.objects.all()
        #Get the list of following/friends
        following = primary_author.following.all()
        fids = [f.followee.id for f in following]

        for a in authors:
            if a.id in fids:
                aids.append(a.id)
        #Get all posts associated

        #1 Get the posts
        #TODO
        i = 0
        authors = Author.objects.filter(id__in=aids)
        posts = Post.objects.filter(author__in=authors).order_by('created_at')
        for post in posts:

            liked = primary_author.likes.filter(post=post)
            if len(liked) == 0:
                liked = 0
            else:
                liked = 1

            if ((post.publicity == 0 and post.unlisted == False) or (post.publicity == 1 and post.author.id == primary_author.id)) or (post.unlisted == True and post.author == primary_author):
                post_serializer = PostSerializer(post, context={'request': request})
                data[i] = post_serializer.data | {'like-count': len(post.likes.all()), 'liked': liked}
                i += 1
            elif post.publicity == 1:
                follow = Follower.objects.get(follower=primary_author, followee=post.author)
                if follow.friendship == True:
                    post_serializer = PostSerializer(post, context={'request': request})
                    data[i] = post_serializer.data | {'like-count': len(post.likes.all()), 'liked': liked}
                    i += 1

        #2 Get the likes
        #TODO - use future outwards facing API for posts and comments

        #2.1 get the likes for posts
        #2.2 get the likes for comments

        #3 Get the comments
        #TODO - comments isnt even done

        #TODO - Sort the data (posts, likes, comments) by timestamp
        
        return Response(data, status=200)
    else:
        return Response(status=401)

@api_view(['GET'])
def getNewInboxInfo(request):
    user = request.user
    if user.is_authenticated:
        data = {}

        #Get the author id for inbox
        aids = []
        primary_author = Author.objects.get(user=user)
        aids.append(primary_author.id)
        #Get the list of authors
        authors = Author.objects.all()
        #Get the list of following/friends
        following = primary_author.following.all()
        fids = [f.followee.id for f in following]

        for a in authors:
            if a.id in fids:
                aids.append(a.id)
        #Get all posts associated

        #1 Get the posts
        #TODO
        i = 0
        oldDate = datetime.now(pytz.timezone('America/Edmonton')) - timedelta(seconds=2)
        authors = Author.objects.filter(id__in=aids)
        posts = Post.objects.filter(author__in=authors, created_at__gte=oldDate).order_by('created_at')
        for post in posts:

            liked = primary_author.likes.filter(post=post)
            if len(liked) == 0:
                liked = 0
            else:
                liked = 1
            
            if ((post.publicity == 0 and post.unlisted == False) or (post.publicity == 1 and aid == primary_author.id)) or (post.unlisted == True and post.author == primary_author):
                post_serializer = PostSerializer(post, context={'request': request})
                data[i] = post_serializer.data | {'like-count': len(post.likes.all()), 'liked': liked}
                i += 1
            elif post.publicity == 1:
                follow = Follower.objects.get(follower=primary_author, followee=post.author)
                if follow.friendship == True:
                    post_serializer = PostSerializer(post, context={'request': request})
                    data[i] = post_serializer.data | {'like-count': len(post.likes.all()), 'liked': liked}
                    i += 1

        #2 Get the likes
        #TODO - use future outwards facing API for posts and comments

        #2.1 get the likes for posts
        #2.2 get the likes for comments

        #3 Get the comments
        #TODO - comments isnt even done

        #TODO - Sort the data (posts, likes, comments) by timestamp
        
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


@api_view(['POST'])
def getPostData(request):
    user = request.user
    if user.is_authenticated:

        primary_author = Author.objects.get(user=user)

        ids = request.data['ids']
        location = request.data['location']

        data = {}
        i = 0
        for post in ids:
            parts = post[2].split('/')
            origin = f'{parts[0]}//{parts[2]}/'

            if origin == location:
                author = Author.objects.get(id=post[1])

                if Post.objects.filter(id=post[0]):
                    post = Post.objects.get(id=post[0])

                    liked = primary_author.likes.filter(post=post)
                    if len(liked) == 0:
                        liked = 0
                    else:
                        liked = 1

                    if ((post.publicity == 0) or (post.publicity == 1 and author.id == primary_author.id)):
                        post_serializer = PostSerializer(post, context={'request': request})
                        data[i] = post_serializer.data | {'like-count': len(post.likes.all()), 'liked': liked}
                        i += 1
                    elif post.publicity == 1:
                        follow = Follower.objects.get(follower=primary_author, followee=author)
                        if follow.friendship == True:
                            post_serializer = PostSerializer(post, context={'request': request})
                            data[i] = post_serializer.data | {'like-count': len(post.likes.all()), 'liked': liked}
                            i += 1

            else:
                #TODO - need to get the updated resource from external node
                pass

        return Response(data, status=200)
    else:
        return Response(status=401)


@api_view(['POST'])
def getDeletedPosts(request):
    user = request.user
    if user.is_authenticated:
        
        ids = request.data['ids']
        location = request.data['location']

        data = {}
        i = 0
        for post in ids:
            parts = post[2].split('/')
            origin = f'{parts[0]}//{parts[2]}/'

            if origin == location:
                if not Post.objects.filter(id=int(post[0])):
                    data[i] = int(post[0])
                    i += 1
            else:
                #TODO - need to check external origin for post (check if 404 or not)
                pass
        
        return Response(data, status=200)
    else:
        return Response(status=401)


@api_view(['GET'])
def getFollowing(request):
    user = request.user
    if user.is_authenticated:
        author = Author.objects.get(user=user)
        following = [x for x in Follower.objects.filter(follower = author)]
        data = {}
        for i, follow in enumerate(following):
            data[i] = {'id': follow.followee.id, 'user': follow.followee.user.username, 'accepted': follow.accepted, 'friendship': follow.friendship}
        return Response(data, status=200)
    return Response(status=401)


@api_view(['GET'])
def getFollowRequests(request):
    user = request.user
    if user.is_authenticated:
        author = Author.objects.get(user=user)
        # Requests that not accepted and not dismissed
        follow_requests = [x for x in Follower.objects.filter(followee = author) if (not x.dismissed and not x.accepted)]
        data = {}
        for i, follow_request in enumerate(follow_requests):
            data[i] = {'id': follow_request.follower.id, 'user': follow_request.follower.user.username}
        return Response(data, status=200)
    return Response(status=401)


@api_view(['POST', 'PUT', 'DELETE'])
def handleFollow(request):
    user = request.user
    if user.is_authenticated:
        author = Author.objects.get(user=user)
        
        # accept/dismiss follow request
        if request.method == 'POST':
            if request.data['action'] == 'accept':
                # FRIENDSHIP CHECKING HERE
                id = request.data['id']
                follower = Author.objects.get(id=id)
                follow_obj = Follower.objects.get(follower = follower, followee = author)
                follow_obj.accepted = True
                follow_obj.save()

                # CHECK FOR FRIENDSHIP
                try:
                    returned_follow_obj = Follower.objects.get(follower = author, followee = follower)
                    returned_follow_obj.friendship = True
                    returned_follow_obj.save()

                    follow_obj.friendship = True
                    follow_obj.save()

                finally:
                    return Response(status=200)
                    

            elif request.data['action'] == 'dismiss':
                id = request.data['id']
                follower = Author.objects.get(id=id)
                follow_obj = Follower.objects.get(follower = follower, followee = author)
                follow_obj.dismissed = True
                follow_obj.save()

                # DISCUSSED DELETION OF FOLLOW OBJ
                follow_obj.delete()
                return Response(status=200)
        
        # put follow request
        elif request.method == 'PUT':
            id = request.data['id']
            followee = Author.objects.get(id=id)
            Follower(follower = author, followee = followee, dismissed = False, accepted = False).save()
            return Response(status=200)
        
        # Used to consider unfollow and dismissal as the same operation,
        # moving dismissal to POST
        elif request.method == 'DELETE':
            # FRIENDSHIP REMOVAL HERE
            id = request.data['id']
            followee = Author.objects.get(id=id)
            Follower.objects.get(follower = author, followee = followee).delete()

            # CHECK FOR FRIENDSHIP
            try:
                returned_follow_obj = Follower.objects.get(follower = followee, followee = author)
                returned_follow_obj.friendship = False
                returned_follow_obj.save()

            finally:
                return Response(status=200)
    return Response(status=401)
                
@api_view(['PUT'])
def updateUser(request, id):
    user = request.user
    if user.is_authenticated and user.id == id:
        
        u = User.objects.get(id=id)
        author = Author.objects.get(user=u)

        author.bio = request.data["bio"]
        author.save()

        u.username = request.data["username"]
        u.save()

        return Response(status=200)
    else:
        return Response(status=401)


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
def authorReqHandler(request, author_id):

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
        return Response(status=200)
    else:
        return Response(status=400)

@api_view(['GET'])
def getFollowers(request, author_id):
    print("service: Get followers request received")
    if author_id == None:
        return Response(status=400)
    
    author = Author.objects.get(id=author_id)

    if author == None:
        return Response(status=404)
    
    followers = author.followed_by.all()
    # get the author instances from the follower instances
    follower_authors = []
    for follower in followers:
        follower_authors.append(follower.follower)


    author_serializer = AuthorSerializer(follower_authors, many=True, context={'request': request})

    serialized_followers = author_serializer.data
    returnDict = {"type": "followers", "items": serialized_followers}

    return Response(returnDict)

@api_view(['GET', 'POST', 'DELETE'])
def followerReqHandler(request, author_id, foreign_author_id):
    print("service: Get follower-followee relationship details request received")
    if foreign_author_id == None or author_id == None:
        return Response(status=400)
    
    followee = Author.objects.get(id=author_id)

    if followee == None:
        return Response(status=404)
    
    if request.method == 'GET':
        relationships_exists = followee.followed_by.filter(follower_id=foreign_author_id).exists()
        return Response(relationships_exists)
    
    # Add FOREIGN_AUTHOR_ID as a follower of AUTHOR_ID (must be authenticated)
    #TODO Allow foriegn keys to remote authors
    elif request.method == 'POST':
        #TODO not sure if they want the follower or the followee to be authenticated
        if not request.user.is_authenticated or request.user != followee.user:
            return Response(status=401)
        follower = Author.objects.get(id=foreign_author_id)
        
        if not Follower.objects.filter(followee=followee, follower=follower).exists():
            Follower.objects.create(followee=followee, follower=follower)


        return Response(status=200)

    # remove FOREIGN_AUTHOR_ID as a follower of AUTHOR_ID
    #TODO Allow foriegn keys to remote authors
    elif request.method == 'DELETE':
        follower = Author.objects.get(id=foreign_author_id)
        follower_instance = Follower.objects.filter(followee=followee, follower=follower).first()

        if follower_instance != None:
            follower_instance.delete()

        return Response(status=200)
    
    # if the request is not GET, POST, or DELETE, return 405
    else:
        return Response(status=405)
            

#TODO Friend / follow request (The spec is unclear on the path for this, so leaving it for later)

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def postReqHandler(request, author_id, post_id):
    if post_id == None:
        print("service: no post id, returning 400 ***********************************************")
        return Response(status=400)
    
    if request.method == 'GET': 
        print("service: Get post request received")
        return getPost(request, post_id)
    
    user = request.user
    if user.is_authenticated:
        if request.method == 'POST':
            print("service: Update post request received")
            return updatePost(request, post_id)

        elif request.method == 'PUT':
            print("service: Create specific post request received")
            return createSpecificPost(request, author_id, post_id)
        
        elif request.method == 'DELETE':
            print("service: Delete post request received")
            return deletePost_1(request, post_id)

        else:
            return Response(status=405)
    else:
        return Response(status=401)

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

#_1 is to avoid name conflict with the deletePost function above
def deletePost_1(request, post_id):
    found_post = Post.objects.get(id=post_id)
    if found_post == None:
        return Response(status=404)
    found_post.delete()
    return Response(status=200)

def createSpecificPost(request, author_id, post_id):
    author = Author.objects.get(id=author_id)
    if author == None:
        return Response(status=404)
    
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
    
    user = request.user
    if user.is_authenticated:

        if request.method == 'POST':
            print("service: Create post request received")
            return createPost(request, author_id)
        elif request.method == 'GET':
            print("service: Get posts request received")
            return getAuthorPosts(request, author_id)
        else:
            return Response(status=405)
    
    else:
        return Response(status=401)
    
#like create specific post, but without the post_id
def createPost(request, author_id):
    author = Author.objects.get(id=author_id)
    if author == None:
        return Response(status=404)
    
    default_origin = f'http://{request.get_host()}/author/{author_id}/'
    #try:

    source = request.data.get('source')
    if source == '':
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

        return Response(status=201)
    else:
        id = request.data.get('post_id')
        
        post = Post.objects.get(id=id)
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

        return Response(status=201)
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

#/service/authors/{AUTHOR_ID}/posts/{POST_ID}/comments
@api_view(['GET', 'POST'])
def commentReqHandler(request, author_id, post_id):
    if post_id == None:
        return Response(status=400)
    
    if request.method == 'GET': 
        print("service: Get comments request received")
        return getComments(request, post_id)
    
    user = request.user
    if user.is_authenticated:
        if request.method == 'POST':
            print("service: Create comment request received")
            return createComment(request, author_id, post_id)

        else:
            return Response(status=405)
    else:
        return Response(status=401)
    
def getComments(request, post_id):
    found_post = Post.objects.filter(id=post_id).first()
    if found_post == None:
        return Response(status=404)
    
    comments = found_post.comments.all().order_by('created_at')

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
    request.data['post_id'] = post_id
    comment_serializer = CommentSerializer(data=request.data, context={'request': request})
    comment_serializer.create(request.data)
    if comment_serializer.is_valid():
        comment_serializer.save()
        return Response(status=200)
    else:
        return Response(status=400)
    
#TODO THIS IS TECHNICALLY THE PARTIALLY DONE INBOX API BUT RIGHT NOW IT JUST REGISTERS SENT LIKES
# /service/authors/{AUTHOR_ID}/inbox/
@api_view(['POST'])
def inboxReqHandler(request, author_id):
    if request.method == 'POST':
        print("service: Inbox POST request received")
        return inboxPOSTHandler(request)
    else:
        return Response(status=405)
    
def inboxPOSTHandler(request):
    data = request.data
    if data['type'] == 'like':
        #TODO write to inbox
        likeSerializer = LikeSerializer(data=data, context={'request': request})
        if likeSerializer.is_valid():
            likeSerializer.save()
            return Response(status=200)
        else:
            print("invalid like", likeSerializer.errors)
            return Response(status=400)
    else:
        return Response(status=400)

#/service/authors/{AUTHOR_ID}/posts/{POST_ID}/likes    
@api_view(['GET'])
def getPostLikes(request, author_id, post_id):
    print("service: Get post likes request received")
    if request.method != 'GET':
        return Response(status=405)

    if post_id == None:
        return Response(status=400)
    
    found_post = Post.objects.filter(id=post_id).first()

    if found_post == None:
        return Response(status=404)
    
    likes = found_post.likes.all().order_by('created_at')
    like_serializer = LikeSerializer(likes, many=True, context={'request': request})
    serialized_likes = like_serializer.data
    return Response(serialized_likes)

#/service/authors/{AUTHOR_ID}/posts/{POST_ID}/comments/{COMMENT_ID}/likes    
@api_view(['GET'])
def getCommentLikes(request, author_id, post_id, comment_id):
    print("service: Get comment likes request received")
    if request.method != 'GET':
        return Response(status=405)

    if post_id == None or comment_id == None:
        return Response(status=400)
    
    found_comment = Comment.objects.filter(id=comment_id).first()

    if found_comment == None:
        return Response(status=404)
    
    likes = found_comment.likes.all().order_by('created_at')
    like_serializer = LikeSerializer(likes, many=True, context={'request': request})
    serialized_likes = like_serializer.data
    return Response(serialized_likes)

#/service/authors/{AUTHOR_ID}/liked
@api_view(['GET'])
def getAuthorLiked(request, author_id):
    print("service: Get author liked request received")
    if request.method != 'GET':
        return Response(status=405)

    if author_id == None:
        return Response(status=400)
    
    found_author = Author.objects.filter(id=author_id).first()

    if found_author == None:
        return Response(status=404)
    
    likes = found_author.likes.all().order_by('created_at')
    like_serializer = LikeSerializer(likes, many=True, context={'request': request})
    serialized_likes = like_serializer.data
    return Response(serialized_likes)