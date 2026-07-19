from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

class LoginViewTest(TestCase):
    """Test login functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_login_page_loads(self):
        """Test login page renders"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
    
    def test_login_with_valid_credentials(self):
        """Test successful login"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        # Regular user redirects to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_with_invalid_credentials(self):
        """Test login with wrong password"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
    
    def test_admin_login_redirects_to_admin_panel(self):
        """Test admin user logs in to admin panel"""
        admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'adminpass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('admin_panel'))


class SignupViewTest(TestCase):
    """Test signup functionality"""
    
    def setUp(self):
        self.client = Client()
    
    def test_signup_page_loads(self):
        """Test signup page renders"""
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signup.html')
    
    def test_signup_with_valid_data(self):
        """Test successful signup"""
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'newpass123',
            'password2': 'newpass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_signup_password_mismatch(self):
        """Test signup with mismatched passwords"""
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'newpass123',
            'password2': 'differentpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Passwords do not match')
        self.assertFalse(User.objects.filter(username='newuser').exists())
    
    def test_signup_duplicate_username(self):
        """Test signup with existing username"""
        User.objects.create_user(username='existing', password='pass123')
        response = self.client.post(reverse('signup'), {
            'username': 'existing',
            'email': 'new@test.com',
            'password': 'newpass123',
            'password2': 'newpass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Username already taken')


class LogoutViewTest(TestCase):
    """Test logout functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_logout_redirects_to_login(self):
        """Test logout redirects to login"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
    
    def test_logout_clears_session(self):
        """Test logout clears user session"""
        self.client.login(username='testuser', password='testpass123')
        self.client.get(reverse('logout'))
        response = self.client.get(reverse('user_dashboard'))
        # Should redirect to login because user is not authenticated
        self.assertEqual(response.status_code, 302)