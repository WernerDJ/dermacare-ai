from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from api.models import BrandPortfolio, Product

class UserDashboardAccessTest(TestCase):
    """Test user dashboard access control"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='user1',
            password='pass123'
        )
    
    def test_dashboard_requires_login(self):
        """Test dashboard redirects unauthenticated users"""
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
    
    def test_dashboard_accessible_to_authenticated_users(self):
        """Test dashboard is accessible to authenticated users"""
        self.client.login(username='user1', password='pass123')
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_dashboard.html')


class UserQuestionTest(TestCase):
    """Test user asking questions"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='user1',
            password='pass123'
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            is_staff=True
        )
        self.client.login(username='user1', password='pass123')
        
        # Create test portfolio and products
        self.portfolio = BrandPortfolio.objects.create(
            name='TestBrand',
            created_by=self.admin
        )
    
    def test_question_without_text(self):
        """Test asking question without text"""
        response = self.client.post(reverse('user_dashboard'), {
            'question': '',
            'brand_ids': [str(self.portfolio.id)],
        })
        self.assertContains(response, 'Please ask a question')
    
    def test_question_without_brand(self):
        """Test asking question without selecting brands"""
        response = self.client.post(reverse('user_dashboard'), {
            'question': 'What products do you recommend?',
            'brand_ids': [],
        })
        self.assertContains(response, 'Please select at least one brand')
    
    def test_portfolio_list_shown(self):
        """Test portfolios are shown in dashboard"""
        response = self.client.get(reverse('user_dashboard'))
        self.assertContains(response, 'TestBrand')


class UserDashboardDisplayTest(TestCase):
    """Test user dashboard displays data correctly"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='user1',
            password='pass123'
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            is_staff=True
        )
        self.client.login(username='user1', password='pass123')
    
    def test_dashboard_shows_all_brands(self):
        """Test dashboard shows all available brands"""
        BrandPortfolio.objects.create(
            name='Biotherm',
            created_by=self.admin,
            total_products=10
        )
        BrandPortfolio.objects.create(
            name='Sensilis',
            created_by=self.admin,
            total_products=15
        )
        
        response = self.client.get(reverse('user_dashboard'))
        self.assertContains(response, 'Biotherm')
        self.assertContains(response, 'Sensilis')
        self.assertContains(response, '10')
        self.assertContains(response, '15')
    
    def test_dashboard_shows_no_brands_message(self):
        """Test dashboard shows message when no brands available"""
        response = self.client.get(reverse('user_dashboard'))
        self.assertContains(response, 'No portfolios available')