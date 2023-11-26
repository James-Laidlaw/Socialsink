from django.test import TestCase
from .models import Author, Follower, Friendship, Post, Comment, Like, Node, ServerSettings
from django.contrib.auth.models import User
from datetime import datetime
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import base64

from django.http import JsonResponse
from rest_framework.response import Response

node_username = "socialsink"
node_password = "password"

credentials = base64.b64encode(f"{node_username}:{node_password}".encode()).decode()

authorized_header = {'Authorization': 'Bearer ' + credentials}



#Testing the models!!
class AuthorModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.author = Author.objects.create(user=self.user)
    
    def test_author_creation(self):
        self.assertEqual(self.author.user, self.user)
        self.assertTrue(isinstance(self.author.created_at, datetime))
    
    def test_followers(self):
        follower = Author.objects.create(user=User.objects.create_user(username='follower', password='followerpassword', email='follow@mail.com'))
        Follower.objects.create(follower=follower, followee=self.author)
        self.assertEqual(self.author.followed_by.first().follower, follower)

    def test_following(self):
        follower = Author.objects.create(user=User.objects.create_user(username='follower', password='followerpassword', email='follow@mail.com'))
        Follower.objects.create(follower=follower, followee=self.author)
        self.assertEqual(follower.follows.first(), self.author)
    
class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.author = Author.objects.create(user=self.user)
    
    def test_post_creation(self):
        post = Post.objects.create(author=self.author, content="Test Content")
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.content, "Test Content")
        self.assertTrue(isinstance(post.created_at, datetime))

    def test_post_ownership(self):
        post = Post.objects.create(author=self.author, content="Test Content")
        self.assertEqual(post, self.author.posts.first())

class CommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.author = Author.objects.create(user=self.user)
        self.authorURL = "http://testserver/service/authors/" + str(self.author.id) + "/"
        self.post = Post.objects.create(author=self.author, content="Test Content")
        self.postURL = "http://testserver/service/authors/" + str(self.author.id) + "/posts/" + str(self.post.id) + "/"
    
    def test_comment_creation(self):
        comment = Comment.objects.create(author_data=self.authorURL, post_endpoint=self.postURL, content="Test Comment")
        self.assertEqual(comment.author_data, self.authorURL)
        self.assertEqual(comment.post_endpoint, self.postURL)
        self.assertEqual(comment.content, "Test Comment")
        self.assertTrue(isinstance(comment.created_at, datetime))

class LikeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.author = Author.objects.create(user=self.user)
        self.post = Post.objects.create(author=self.author, content="Test Content")
        self.authorURL = "http://testserver/service/authors/" + str(self.author.id) + "/"
        self.postURL = "http://testserver/service/authors/" + str(self.author.id) + "/posts/" + str(self.post.id) + "/"

    
    def test_like_creation(self):
        like = Like.objects.create(author_endpoint=self.authorURL, post_endpoint=self.postURL)
        self.assertEqual(like.author_endpoint, self.authorURL)
        self.assertEqual(like.post_endpoint, self.postURL)
        self.assertTrue(isinstance(like.created_at, datetime))

    def test_like_on_comment(self):
        comment = Comment.objects.create(author_data=self.authorURL, post_endpoint=self.post, content="Test Comment")
        commentURL = "http://testserver/service/authors/" + str(self.author.id) + "/posts/" + str(self.post.id) + "/comments/" + str(comment.id) + "/"
        like = Like.objects.create(author_endpoint=self.authorURL, comment_endpoint=commentURL)
        self.assertEqual(like.author_endpoint, self.authorURL)
        self.assertEqual(like.comment_endpoint, commentURL)



#Testing the APIS!!
class YourApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.author = Author.objects.create(user=self.user)
        self.authorURL = "http://testserver/service/authors/" + str(self.author.id) + "/"
        self.node = Node.objects.create(hostname="http://testserver/", username=node_username, password=node_password)
    #utility
    def make_secondary_author(self):
        user = User.objects.create_user(username='testuser2', password='testpassword', email="testUserEmail@email.com")
        author = Author.objects.create(user=user)
        return author
    
    def get_author_URL(self, author):
        return 'http://testserver/service/authors/' + str(author.id) + '/'
    
    def get_post_URL(self, author, post):
        return self.get_author_URL(author) + 'posts/' + str(post.id) + '/'
    
    def get_comment_URL(self, author, post, comment):
        return self.get_post_URL(author, post) + 'comments/' + str(comment.id) + '/'
    

    
    def check_author(self, author, json):
        self.assertEqual(json['type'], 'author')
        self.assertEqual(json['id'], self.get_author_URL(author))
        self.assertEqual(json['url'], self.get_author_URL(author))
        self.assertEqual(json['host'], 'http://testserver/')
        self.assertEqual(json['displayName'], author.user.username)
        self.assertEqual(json['github'], None)
        self.assertEqual(json['profileImage'], None)
    
    def check_post(self, post, json):
        self.assertEqual(json['type'], 'post')
        self.assertEqual(json['id'], self.get_post_URL(post.author, post))
        self.assertEqual(json['title'], 'Default title')
        self.assertEqual(json['description'], None)
        self.assertEqual(json['contentType'], 'text/plain')
        self.assertEqual(json['content'], post.content)
        self.check_author(post.author, json['author'])
        self.assertEqual(json['published'], post.created_at.isoformat())
        self.assertEqual(json['visibility'], 'PUBLIC')
        self.assertEqual(json['unlisted'], False)
        self.assertEqual(json['comments'], self.get_post_URL(post.author, post) + 'comments')

    def test_sign_up(self):
        server_settings = ServerSettings.objects.create(auto_permit_users=True)
        url = reverse('createAccount')
        # EMAIL MUST BE UNIQUE (CANNOT EXIST ALREADY)
        data = {'username': 'unique_testuser', 'email': 'unique_test_email@mail.com', 'password': 'testpassword'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_login_request(self):
        url = reverse('loginRequest')
        data = {'username': 'testuser', 'password': 'testpassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_logout_request(self):
        url = reverse('logoutRequest')
        response = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_account(self):
        url = reverse('deleteAccount')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # tests for outward facing API (/service/*)

    #GET /service/authors/
    def test_get_authors(self):
        url = reverse('authorList')
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # #GET /service/authors/<str:author_id>/
    def test_get_author(self):
        url = reverse('authorReqHandler', args=[self.author.id])
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_author(self.author, response.json())

    #POST /service/authors/<str:author_id>/ //only for updating, not creating
    def test_update_author(self):
        url = reverse('authorReqHandler', args=[self.author.id])
        data = {'displayName': 'testuser2'}
        
        # try to update without authentication
        response: Response = self.client.post(url, data, format='json', headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # try to update with authentication
        self.client.force_authenticate(user=self.user)
        response: Response = self.client.post(url, data, format='json', headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "update with authentication failed")
        #check if the author was updated
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK, "get author failed")
        self.assertEqual(response.json()['displayName'], 'testuser2')

    #GET /service/authors/<str:author_id>/followers
    def test_get_followers(self):
        follower = self.make_secondary_author()
        Follower.objects.create(follower=follower, followee=self.author)
        url = reverse('getFollowers', args=[self.author.id])
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['type'], 'followers')
        self.check_author(follower, response.json()['items'][0])


    #GET /service/authors/<str:author_id>/followers/<str:foreign_author_id>
    def test_get_follower(self):
        follower = self.make_secondary_author()
        Follower.objects.create(follower=follower, followee=self.author)
        url = reverse('followerReqHandler', args=[self.author.id, follower.id])
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), True)
    
    #POST /service/authors/<str:author_id>/followers/<str:foreign_author_id>
    def test_add_follower(self):
        follower = self.make_secondary_author()
        url = reverse('followerReqHandler', args=[self.author.id, follower.id])
        response: JsonResponse = self.client.post(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response: JsonResponse = self.client.post(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #check if the follower was added
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), True)
    
    #DELETE /service/authors/<str:author_id>/followers/<str:foreign_author_id>
    def test_remove_follower(self):
        follower = self.make_secondary_author()
        url = reverse('followerReqHandler', args=[self.author.id, follower.id])
        response: JsonResponse = self.client.delete(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    #PUT /service/authors/<str:author_id>/followers/<str:foreign_author_id>
    def test_follower_req_bad_method(self):
        follower = self.make_secondary_author()
        url = reverse('followerReqHandler', args=[self.author.id, follower.id])
        response: JsonResponse = self.client.put(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    #GET /service/authors/<str:author_id>/posts/
    def test_get_post(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        url = reverse('postReqHandler', args=[self.author.id, post.id])
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_post(post, response.json())
    
    #POST /service/authors/<str:author_id>/posts/<str:post_id> (update post (for some reason))
    def test_update_post(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        url = reverse('postReqHandler', args=[self.author.id, post.id])
        data = {'title': 'New Title'}
        response: JsonResponse = self.client.post(url, data, format='json', headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response: JsonResponse = self.client.post(url, data, format='json', headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], 'New Title')

    #DELETE /service/authors/<str:author_id>/posts/<str:post_id>
    def test_delete_post(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        url = reverse('postReqHandler', args=[self.author.id, post.id])
        response: JsonResponse = self.client.delete(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    #PUT /service/authors/<str:author_id>/posts/<str:post_id>
    def test_create_specific_post(self):
        url = reverse('postReqHandler', args=[self.author.id, 12345])
        data = {'title': 'New Title', 'content': 'Test post content', 'publicity': 'public'}
        response: JsonResponse = self.client.put(url, data, format='json', headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response: JsonResponse = self.client.put(url, data, format='json', headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], 'New Title')

    #GET /service/authors/<str:author_id>/posts/
    def test_get_posts(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        url = reverse('postCreationReqHandler', args=[self.author.id])
        self.client.force_authenticate(user=self.user)
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_post(post, response.json()[0])

    #POST /service/authors/<str:author_id>/posts/
    def test_create_post(self):
        url = reverse('postCreationReqHandler', args=[self.author.id])
        data = {'title': 'New Title', 'content': 'Test post content', 'publicity': 'public'}
        response: JsonResponse = self.client.post(url, data, format='json', headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response: JsonResponse = self.client.post(url, data, format='json', headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response: JsonResponse = self.client.get(url,  headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['title'], 'New Title')

    #GET /service/authors/<str:author_id>/posts/<str:post_id>/comments/
    def test_get_comments(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        postURL = self.get_post_URL(self.author, post)
        comment = Comment.objects.create(author_data=self.authorURL, post_endpoint=postURL, content='Test comment')
        url = reverse('commentReqHandler', args=[self.author.id, post.id])
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['comment'], 'Test comment')

    #POST /service/authors/<str:author_id>/posts/<str:post_id>/comments/
    def test_create_comment(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        url = reverse('commentReqHandler', args=[self.author.id, post.id])
        data = {'comment': 'Test comment', "author": {"id": self.authorURL}}
        response: JsonResponse = self.client.post(url, data, format='json', headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['comment'], 'Test comment')

    # POST /service/authors/{AUTHOR_ID}/inbox/
    def test_send_like_inbox(self):
        post = Post.objects.create(
            author=self.author, content="Test post content", publicity=0
        )
        url = reverse("inboxReqHandler", args=[self.author.id])
        data = {
            "@context": "https://www.w3.org/ns/activitystreams",
            "summary": "test summary",
            "type": "Like",
            "author": {
                "type": "author",
                "id": self.authorURL,
                "host": "http://testserver/",
                "displayName": self.author.user.username,
                "url": self.authorURL,
            },
            "object": self.get_post_URL(self.author, post),
        }
        response: JsonResponse = self.client.post(url, data, format="json", headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    #GET /service/authors/{AUTHOR_ID}/posts/{POST_ID}/likes/
    def test_get_post_likes(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        postURL = self.get_post_URL(self.author, post)
        like = Like.objects.create(author_endpoint=self.authorURL, post_endpoint=postURL)
        url = reverse('likeReqHandler', args=[self.author.id, post.id])
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['author'], self.authorURL)
    
    #GET /service/authors/{AUTHOR_ID}/posts/{POST_ID}/comments/{COMMENT_ID}/likes/
    def test_get_comment_likes(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        postURL = self.get_post_URL(self.author, post)
        comment = Comment.objects.create(author_data=self.authorURL, post_endpoint=postURL, content='Test comment')
        like = Like.objects.create(author_endpoint=self.authorURL, post_endpoint=postURL)
        url = reverse('commentLikeReqHandler', args=[self.author.id, post.id, comment.id])
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['author'], self.authorURL)
       
    #GET /service/authors/{AUTHOR_ID}/liked/
    def test_get_author_liked(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        postURL = self.get_post_URL(self.author, post)
        like = Like.objects.create(author_endpoint=self.authorURL, post_endpoint=postURL)
        url = reverse('authorLikedReqHandler', args=[self.author.id])
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['object'], postURL)

    def test_send_post_inbox(self):
        post = Post.objects.create(
            author=self.author, content="Test post content", publicity=0
        )
        url = reverse("inboxReqHandler", args=[self.author.id])
        author_id = self.authorURL
        data = {
            "xyz": "all of this should be stored arbitrarily, nothing is needed other than type",
            "type": "Post",
            "author": {
                "type": "author",
                "id": author_id,
                "host": "http://testserver/",
                "displayName": self.author.user.username,
                "url": author_id,
            },
            "id": self.get_post_URL(self.author, post)
        }
        response: JsonResponse = self.client.post(url, data, format="json", headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_send_Follow_inbox(self):
        follower = self.make_secondary_author()
        url = reverse("inboxReqHandler", args=[self.author.id])
        author_id = self.authorURL
        data = {
            "xyz": "all of this should be stored arbitrarily, nothing is needed other than type",
            "type": "Follow",
            "author": {
                "type": "author",
                "id": author_id,
                "host": "http://testserver/",
                "displayName": self.author.user.username,
                "url": author_id,
            },
        }
        self.client.force_authenticate(user=follower.user)
        response: JsonResponse = self.client.post(url, data, format="json", headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_send_comment_inbox(self):
        post = Post.objects.create(
            author=self.author, content="Test post content", publicity=0
        )
        postURL = self.get_post_URL(self.author, post)
        comment = Comment.objects.create(
            author_data=self.authorURL, post_endpoint=postURL, content="Test comment"
        )
        commentURL = self.get_comment_URL(self.author, post, comment)
        url = reverse("inboxReqHandler", args=[self.author.id])
        author_id = "http://testserver/service/authors/" + str(self.author.id) + "/"
        data = {
            "xyz": "all of this should be stored arbitrarily, nothing is needed other than type",
            "id": commentURL,
            "type": "Comment",
            "author": {
                "type": "author",
                "id": author_id,
                "host": "http://testserver/",
                "displayName": self.author.user.username,
                "url": author_id,
            },
            "object": "http://testserver/service/authors/" + str(self.author.id) + "/posts/" + str(post.id) + "/comments/" + str(comment.id) + "/",
        }
        response: JsonResponse = self.client.post(url, data, format="json", headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_inbox(self):
        self.test_send_comment_inbox()
        self.test_send_post_inbox()
        # self.test_send_Follow_inbox()
        self.test_send_like_inbox()
        url = reverse("inboxReqHandler", args=[self.author.id])
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inbox_items = response.json()["items"]

        self.assertEqual(len(inbox_items), 3) #TODO change this to 4 when we have follows working
        self.assertEqual(inbox_items[0]["type"], "Like")
        # self.assertEqual(inbox_items[1]["type"], "Follow")
        self.assertEqual(inbox_items[1]["type"], "Post")
        self.assertEqual(inbox_items[2]["type"], "Comment")
    
    def test_delete_inbox(self):
        self.test_get_inbox()
        url = reverse("inboxReqHandler", args=[self.author.id])
        response: JsonResponse = self.client.delete(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response: JsonResponse = self.client.get(url, headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inbox_items = response.json()["items"]
        self.assertEqual(len(inbox_items), 0)

    def test_get_inbox_pagination(self):
        self.test_send_comment_inbox()
        self.test_send_post_inbox()
        self.test_send_like_inbox()
        url = reverse("inboxReqHandler", args=[self.author.id])
        data = {"page": 1, "size": 2}
        self.client.force_authenticate(user=self.user)
        response: JsonResponse = self.client.get(url, data, format="json", headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inbox_items = response.json()["items"]

        self.assertEqual(len(inbox_items), 2)
        self.assertEqual(inbox_items[0]["type"], "Like")
        self.assertEqual(inbox_items[1]["type"], "Post")

        data = {"page": 2, "size": 2}
        response: JsonResponse = self.client.get(url, data, format="json", headers=authorized_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inbox_items = response.json()["items"]

        self.assertEqual(len(inbox_items), 1)
        self.assertEqual(inbox_items[0]["type"], "Comment")


