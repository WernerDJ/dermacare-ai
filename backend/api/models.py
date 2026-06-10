from django.db import models
from django.contrib.auth.models import User
import json

class BrandPortfolio(models.Model):
    """
    Represents a brand's product portfolio analysis
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='portfolios')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    # Metadata
    total_products = models.IntegerField(default=0)
    products_with_ingredients = models.IntegerField(default=0)
    analysis_file = models.FileField(upload_to='analyses/', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_date']
        verbose_name_plural = 'Brand Portfolios'
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Individual product within a brand portfolio
    """
    portfolio = models.ForeignKey(BrandPortfolio, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    benefits = models.TextField(blank=True)
    how_to_use = models.TextField(blank=True)
    pdf_ingredients = models.TextField(blank=True, help_text="Ingredients found in PDF")
    
    class Meta:
        unique_together = ('portfolio', 'name')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.portfolio.name} - {self.name}"


class Ingredient(models.Model):
    """
    Ingredients for a product (from APIs and fallbacks)
    """
    SOURCE_CHOICES = [
        ('pdf', 'PDF Document'),
        ('upc_inci', 'UPC ItemDB + INCIApi'),
        ('gemini', 'Gemini Fallback'),
    ]
    
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='ingredient')
    ingredients_list = models.TextField(help_text="Comma-separated INCI ingredients")
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='pdf')
    barcode = models.CharField(max_length=20, blank=True, help_text="UPC/EAN barcode")
    quality_score = models.IntegerField(null=True, blank=True, help_text="INCIApi quality score")
    found_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Ingredients'
    
    def __str__(self):
        return f"{self.product.name} - {self.source}"


class AnalysisTask(models.Model):
    """
    Track background analysis tasks (for Celery)
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    task_id = models.CharField(max_length=255, unique=True)
    portfolio = models.ForeignKey(BrandPortfolio, on_delete=models.CASCADE, related_name='tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)
    current_step = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.portfolio.name} - {self.status}"


class UserSession(models.Model):
    """
    Track user's selected brands for context
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dermacare_session')
    selected_portfolios = models.ManyToManyField(BrandPortfolio, blank=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s session"
