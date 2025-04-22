from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()


class UserRegistrationViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('register') 

    def test_user_registration(self):
        data = {
            'username': 'testuser@example.com',
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
        self.assertTrue(User.objects.filter(username='testuser@example.com').exists())


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


