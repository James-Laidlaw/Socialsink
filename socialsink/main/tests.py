from django.test import TestCase
from .models import Author, Follower, Friendship, Post, Comment, Like
from django.contrib.auth.models import User
from datetime import datetime
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from django.http import JsonResponse
from rest_framework.response import Response

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
        self.post = Post.objects.create(author=self.author, content="Test Content")
    
    def test_comment_creation(self):
        comment = Comment.objects.create(author=self.author, post=self.post, content="Test Comment")
        self.assertEqual(comment.author, self.author)
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.content, "Test Comment")
        self.assertTrue(isinstance(comment.created_at, datetime))

    def test_comment_ownership(self):
        comment = Comment.objects.create(author=self.author, post=self.post, content="Test Comment")
        self.assertEqual(self.author.comments.first(), comment)
        self.assertEqual(self.post.comments.first(), comment)

class LikeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.author = Author.objects.create(user=self.user)
        self.post = Post.objects.create(author=self.author, content="Test Content")
    
    def test_like_creation(self):
        like = Like.objects.create(author=self.author, post=self.post)
        self.assertEqual(like.author, self.author)
        self.assertEqual(like.post, self.post)
        self.assertTrue(isinstance(like.created_at, datetime))

    def test_like_ownership(self):
        like = Like.objects.create(author=self.author, post=self.post)
        self.assertEqual(self.author.likes.first(), like)
        self.assertEqual(self.post.likes.first(), like)

    def test_like_on_comment(self):
        comment = Comment.objects.create(author=self.author, post=self.post, content="Test Comment")
        like = Like.objects.create(author=self.author, comment=comment)
        self.assertEqual(self.author.likes.first(), like)
        self.assertEqual(comment.likes.first(), like)


#Testing the APIS!!
class YourApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.author = Author.objects.create(user=self.user)

    #utility
    def make_secondary_author(self):
        user = User.objects.create_user(username='testuser2', password='testpassword', email="testUserEmail@email.com")
        author = Author.objects.create(user=user)
        return author
    
    def check_author(self, author, json):
        self.assertEqual(json['type'], 'author')
        self.assertEqual(json['id'], 'http://testserver/service/authors/' + str(author.id) + '/')
        self.assertEqual(json['url'], 'http://testserver/service/authors/' + str(author.id) + '/')
        self.assertEqual(json['host'], 'http://testserver/')
        self.assertEqual(json['displayName'], author.user.username)
        self.assertEqual(json['github'], None)
        self.assertEqual(json['profileImage'], None)
    
    def check_post(self, post, json):
        self.assertEqual(json['type'], 'post')
        self.assertEqual(json['id'], 'http://testserver/service/authors/' + str(post.author.id) + '/posts/' + str(post.id) + '/')
        self.assertEqual(json['title'], 'Default title')
        self.assertEqual(json['description'], None)
        self.assertEqual(json['contentType'], 'text/plain')
        self.assertEqual(json['content'], post.content)
        self.check_author(post.author, json['author'])
        self.assertEqual(json['published'], post.created_at.isoformat())
        self.assertEqual(json['visibility'], 'PUBLIC')
        self.assertEqual(json['unlisted'], False)

    def test_sign_up(self):
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
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_old_available_posts(self):
        url = reverse('getOldAvailablePosts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_account(self):
        url = reverse('deleteAccount')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_like_post(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        url = reverse('likePost', args=[post.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_post_data(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        like = Like.objects.create(author=self.author, post=post)
        url = reverse('getPostData', args=[post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(int(response.data['count']), 1)
        self.assertEqual(response.data['content'], 'Test post content')
        self.assertEqual(response.data['edited'], False)

    def test_delete_post(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        url = reverse('deletePost', args=[post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # tests for outward facing API (/service/*)

    #GET /service/authors/
    def test_get_authors(self):
        url = reverse('authorList')
        response: JsonResponse = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # #GET /service/authors/<str:author_id>/
    def test_get_author(self):
        url = reverse('authorReqHandler', args=[self.author.id])
        response: JsonResponse = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_author(self.author, response.json())

    #POST /service/authors/<str:author_id>/ //only for updating, not creating
    def test_update_author(self):
        url = reverse('authorReqHandler', args=[self.author.id])
        data = {'displayName': 'testuser2'}
        
        # try to update without authentication
        response: Response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # try to update with authentication
        self.client.force_authenticate(user=self.user)
        response: Response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #check if the author was updated
        response: JsonResponse = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['displayName'], 'testuser2')

    #GET /service/authors/<str:author_id>/followers
    def test_get_followers(self):
        follower = self.make_secondary_author()
        Follower.objects.create(follower=follower, followee=self.author)
        url = reverse('getFollowers', args=[self.author.id])
        response: JsonResponse = self.client.get(url)
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['type'], 'followers')
        self.check_author(follower, response.json()['items'][0])


    #GET /service/authors/<str:author_id>/followers/<str:foreign_author_id>
    def test_get_follower(self):
        follower = self.make_secondary_author()
        Follower.objects.create(follower=follower, followee=self.author)
        url = reverse('followerReqHandler', args=[self.author.id, follower.id])
        response: JsonResponse = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), True)
    
    #POST /service/authors/<str:author_id>/followers/<str:foreign_author_id>
    def test_add_follower(self):
        follower = self.make_secondary_author()
        url = reverse('followerReqHandler', args=[self.author.id, follower.id])
        response: JsonResponse = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response: JsonResponse = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #check if the follower was added
        response: JsonResponse = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), True)
    
    #DELETE /service/authors/<str:author_id>/followers/<str:foreign_author_id>
    def test_remove_follower(self):
        follower = self.make_secondary_author()
        url = reverse('followerReqHandler', args=[self.author.id, follower.id])
        response: JsonResponse = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    #PUT /service/authors/<str:author_id>/followers/<str:foreign_author_id>
    def test_follower_req_bad_method(self):
        follower = self.make_secondary_author()
        url = reverse('followerReqHandler', args=[self.author.id, follower.id])
        response: JsonResponse = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    #GET /service/authors/<str:author_id>/posts/
    def test_get_post(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        url = reverse('postReqHandler', args=[self.author.id, post.id])
        response: JsonResponse = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_post(post, response.json())
    
    #POST /service/authors/<str:author_id>/posts/<str:post_id> (update post (for some reason))
    def test_update_post(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        url = reverse('postReqHandler', args=[self.author.id, post.id])
        data = {'title': 'New Title'}
        response: JsonResponse = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response: JsonResponse = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response: JsonResponse = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], 'New Title')

    #DELETE /service/authors/<str:author_id>/posts/<str:post_id>
    def test_delete_post(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        url = reverse('postReqHandler', args=[self.author.id, post.id])
        self.client.force_authenticate(user=self.user)
        response: JsonResponse = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    #PUT /service/authors/<str:author_id>/posts/<str:post_id>
    def test_create_specific_post(self):
        url = reverse('postReqHandler', args=[self.author.id, 12345])
        data = {'title': 'New Title', 'content': 'Test post content', 'publicity': 'public'}
        response: JsonResponse = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response: JsonResponse = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response: JsonResponse = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], 'New Title')

    #GET /service/authors/<str:author_id>/posts/
    def test_get_posts(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        url = reverse('postCreationReqHandler', args=[self.author.id])
        self.client.force_authenticate(user=self.user)
        response: JsonResponse = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.json())
        self.check_post(post, response.json()[0])

    #POST /service/authors/<str:author_id>/posts/
    def test_create_post(self):
        url = reverse('postCreationReqHandler', args=[self.author.id])
        data = {'title': 'New Title', 'content': 'Test post content', 'publicity': 'public'}
        response: JsonResponse = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response: JsonResponse = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response: JsonResponse = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]['title'], 'New Title')
       

    