from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from api.models import BrandPortfolio, AnalysisTask

class AdminPanelAccessTest(TestCase):
    """Test admin panel access control"""
    
    def setUp(self):
        self.client = Client()
        self.regular_user = User.objects.create_user(
            username='regular',
            password='pass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            password='pass123',
            is_staff=True
        )
    
    def test_admin_panel_requires_login(self):
        """Test admin panel redirects unauthenticated users"""
        response = self.client.get(reverse('admin_panel'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
    
    def test_admin_panel_requires_staff(self):
        """Test admin panel rejects non-staff users"""
        self.client.login(username='regular', password='pass123')
        response = self.client.get(reverse('admin_panel'))
        self.assertEqual(response.status_code, 302)
    
    def test_admin_panel_accessible_to_staff(self):
        """Test admin panel is accessible to staff"""
        self.client.login(username='admin', password='pass123')
        response = self.client.get(reverse('admin_panel'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_panel.html')


class PortfolioUploadTest(TestCase):
    """Test portfolio upload functionality"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='pass123',
            is_staff=True
        )
        self.client.login(username='admin', password='pass123')
    
    def test_upload_form_validation_brand_name(self):
        """Test upload fails without brand name"""
        doc = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        response = self.client.post(reverse('admin_panel'), {
            'action': 'upload',
            'brand_name': '',
            'product_names': 'Product 1\nProduct 2',
            'document': doc,
        }, follow=True)
        self.assertContains(response, 'Brand name is required')
        self.assertEqual(BrandPortfolio.objects.count(), 0)
    
    def test_upload_form_validation_products(self):
        """Test upload fails without product names"""
        doc = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        response = self.client.post(reverse('admin_panel'), {
            'action': 'upload',
            'brand_name': 'TestBrand',
            'product_names': '',
            'document': doc,
        }, follow=True)
        self.assertContains(response, 'Please enter at least one product name')
    
    def test_upload_form_validation_document(self):
        """Test upload fails without document"""
        response = self.client.post(reverse('admin_panel'), {
            'action': 'upload',
            'brand_name': 'TestBrand',
            'product_names': 'Product 1\nProduct 2',
        }, follow=True)
        self.assertContains(response, 'Document is required')
    
    def test_upload_creates_portfolio(self):
        """Test successful upload creates portfolio"""
        doc = SimpleUploadedFile(
            "test.txt",
            b"Test content",
            content_type="text/plain"
        )
        response = self.client.post(reverse('admin_panel'), {
            'action': 'upload',
            'brand_name': 'Biotherm',
            'product_names': 'Product 1\nProduct 2',
            'document': doc,
            'lookup_ingredients': 'on',
        }, follow=True)
        
        self.assertTrue(BrandPortfolio.objects.filter(name='Biotherm').exists())
        portfolio = BrandPortfolio.objects.get(name='Biotherm')
        self.assertEqual(portfolio.created_by, self.admin_user)
        self.assertEqual(response.status_code, 200)


class PortfolioDeleteTest(TestCase):
    """Test portfolio deletion"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='pass123',
            is_staff=True
        )
        self.client.login(username='admin', password='pass123')
        
        self.portfolio = BrandPortfolio.objects.create(
            name='TestBrand',
            created_by=self.admin_user
        )
    
    def test_delete_portfolio(self):
        """Test portfolio deletion"""
        response = self.client.post(reverse('admin_panel'), {
            'action': 'delete',
            'portfolio_id': self.portfolio.id,
        }, follow=True)
        
        self.assertFalse(BrandPortfolio.objects.filter(id=self.portfolio.id).exists())
        self.assertContains(response, 'deleted')
    
    def test_delete_nonexistent_portfolio(self):
        """Test deleting non-existent portfolio"""
        response = self.client.post(reverse('admin_panel'), {
            'action': 'delete',
            'portfolio_id': 99999,
        })
        self.assertEqual(response.status_code, 302)


class AdminPanelDisplayTest(TestCase):
    """Test admin panel displays data correctly"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            password='pass123',
            is_staff=True
        )
        self.client.login(username='admin', password='pass123')
    
    def test_admin_panel_shows_portfolios(self):
        """Test admin panel displays portfolios"""
        BrandPortfolio.objects.create(
            name='Biotherm',
            created_by=self.admin_user,
            total_products=10
        )
        BrandPortfolio.objects.create(
            name='Sensilis',
            created_by=self.admin_user,
            total_products=15
        )
        
        response = self.client.get(reverse('admin_panel'))
        self.assertContains(response, 'Biotherm')
        self.assertContains(response, 'Sensilis')
        self.assertContains(response, '10')
        self.assertContains(response, '15')
    
    def test_admin_panel_shows_tasks(self):
        """Test admin panel displays analysis tasks"""
        portfolio = BrandPortfolio.objects.create(
            name='TestBrand',
            created_by=self.admin_user
        )
        task = AnalysisTask.objects.create(
            task_id='test-task-123',
            portfolio=portfolio,
            status='processing',
            progress=50
        )
        
        response = self.client.get(reverse('admin_panel'))
        self.assertContains(response, 'TestBrand')
        self.assertContains(response, 'processing')
        self.assertContains(response, '50')
