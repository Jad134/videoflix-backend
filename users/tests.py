from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from content.models import Video
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

# Create your tests here.
class UserRegistrationViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('register') 

    def test_user_registration(self):
        data = {
            'username': 'testuser',
            'password': 'password123',
            'first_name': 'Jad',
            'last_name': 'LaLa',
            'email': 'testuser@example.com',
            'custom': 'Custom Field Value',
            'address': '123 Test Street',
            'phone': '1234567890'
        }
        response = self.client.post(self.url, data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='testuser').exists())


class CheckUsernameViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_username_available(self):
        url = reverse('check-username', args=['check-username'])  
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['exists'])

    def test_username_taken(self):
        User.objects.create_user(username='existinguser', password='testpassword')
        url = reverse('check-username', args=['existinguser'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['exists'])



class ActivateAccountViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_activate_user(self):
        user = User.objects.create_user(username='testuser', password='testpassword', is_active=False)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        url = reverse('activate', kwargs={'uidb64': uidb64, 'token': token}) 
        response = self.client.get(url)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(response.status_code, 200)


class UserLoginViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_user_login_success(self):
        url = reverse('login')  
        data = {'username': 'testuser', 'password': 'testpassword'}
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Login successful.', response.json()['message'])

    def test_user_login_failure(self):
        url = reverse('login')
        data = {'username': 'testuser', 'password': 'wrongpassword'}
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid credentials.', response.json()['detail'])


class UserFavoritesByIdViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        video_file = SimpleUploadedFile('test_video.mp4', b'test video content')
        self.video1 = Video.objects.create(title='Test Video 1', description='A test video 1.', video_file=video_file)
        self.video2 = Video.objects.create(title='Test Video 2', description='A test video 2.', video_file=video_file)
        self.user.favorite_videos.add(self.video1, self.video2)

    def test_get_user_favorites(self):
        url = reverse('user-favorites-by-id', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertIn(self.video1.id, response.json())
        self.assertIn(self.video2.id, response.json())
