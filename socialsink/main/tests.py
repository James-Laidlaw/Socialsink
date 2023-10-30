from django.test import TestCase
from .models import Author, Follower, Friendship, Post, Comment, Like
from django.contrib.auth.models import User
from datetime import datetime
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


#Testing the models!!
class AuthorModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.author = Author.objects.create(user=self.user)
    
    def test_author_creation(self):
        self.assertEqual(self.author.user, self.user)
        self.assertTrue(isinstance(self.author.created_at, datetime))
    
    def test_followers(self):
        follower = Author.objects.create(user=User.objects.create_user(username='follower', password='followerpassword'))
        Follower.objects.create(follower=follower, followee=self.author)
        self.assertEqual(self.author.followed_by.first().follower, follower)

    def test_following(self):
        follower = Author.objects.create(user=User.objects.create_user(username='follower', password='followerpassword'))
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

    def test_get_like_count(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        like = Like.objects.create(author=self.author, post=post)
        url = reverse('getLikeCount', args=[post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(int(response.data['count']), 1)

    def test_delete_post(self):
        post = Post.objects.create(author=self.author, content='Test post content', publicity=0)
        url = reverse('deletePost', args=[post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)