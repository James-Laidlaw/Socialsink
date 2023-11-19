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

    def test_make_post(self):
        url = reverse('makePost')
        data = {'text': 'Test post content', 'publicity': 'public'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

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

    def test_update_post_data(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        like = Like.objects.create(author=self.author, post=post)
        data = {'text': 'New text for post'}
        url = reverse('updatePostData', args=[post.id])
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

    #GET /service/authors/<str:author_id>/
    def test_get_author(self):
        url = reverse('authorDetail', args=[self.author.id])
        response: JsonResponse = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['id'], 'http://testserver/service/authors/1/')
        self.assertEqual(response.json()['url'], 'http://testserver/service/authors/1/')
        self.assertEqual(response.json()['host'], 'http://testserver/')
        self.assertEqual(response.json()['displayName'], 'testuser')
        self.assertEqual(response.json()['github'], None)
        self.assertEqual(response.json()['profileImage'], None)

    #POST /service/authors/<str:author_id>/ //only for updating, not creating
    def test_update_author(self):
        url = reverse('authorDetail', args=[self.author.id])
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

