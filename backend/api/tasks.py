from celery import shared_task
from django.utils import timezone
import json
import os
from pathlib import Path
from .models import BrandPortfolio, Product, Ingredient, AnalysisTask
import google.generativeai as genai
from django.conf import settings

@shared_task(bind=True)
def analyze_portfolio_task(self, portfolio_id, pdf_path, lookup_ingredients=True):
    """
    Celery task to analyze PDF and extract products
    """
    try:
        portfolio = BrandPortfolio.objects.get(id=portfolio_id)
        analysis_task = AnalysisTask.objects.get(portfolio=portfolio, status='pending')
        
        # Update status
        analysis_task.status = 'processing'
        analysis_task.current_step = 'Extracting products from PDF...'
        analysis_task.save()
        
        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 3})
        
        # Extract products from PDF
        products_data = extract_products_from_document(pdf_path, portfolio)
        portfolio.total_products = len(products_data)
        
        # Lookup ingredients if requested
        if lookup_ingredients:
            analysis_task.current_step = 'Looking up ingredients...'
            analysis_task.progress = 50
            analysis_task.save()
            
            self.update_state(state='PROGRESS', meta={'current': 2, 'total': 3})
            
            ingredients_lookup = lookup_product_ingredients(products_data)
            portfolio.products_with_ingredients = sum(1 for ing in ingredients_lookup.values() if ing)
        
        # Save results
        analysis_task.current_step = 'Saving results...'
        analysis_task.progress = 90
        analysis_task.save()
        
        self.update_state(state='PROGRESS', meta={'current': 3, 'total': 3})
        
        # Save portfolio as JSON
        save_portfolio_as_json(portfolio, products_data, ingredients_lookup if lookup_ingredients else {})
        
        # Mark as complete
        analysis_task.status = 'completed'
        analysis_task.progress = 100
        analysis_task.completed_date = timezone.now()
        analysis_task.save()
        
        return {'status': 'success', 'portfolio_id': portfolio_id}
        
    except Exception as e:
        try:
            analysis_task = AnalysisTask.objects.get(portfolio__id=portfolio_id)
            analysis_task.status = 'failed'
            analysis_task.error_message = str(e)
            analysis_task.completed_date = timezone.now()
            analysis_task.save()
        except:
            pass
        
        raise

def extract_products_from_document(pdf_path, portfolio):
    """Extract products from PDF using Gemini - WITHOUT upload_file"""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Read PDF as binary
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    prompt = """
    Extract ALL products from this PDF document.
    For each product, provide:
    1. Product name
    2. Description (2-3 sentences)
    3. Category (skincare, makeup, etc)
    4. Benefits (comma-separated)
    5. How to use (brief)
    
    Return ONLY as JSON array with fields: name, description, category, benefits, how_to_use, ingredients
    
    Example: [{"name":"Product A","description":"...","category":"...","benefits":"...","how_to_use":"...","ingredients":"..."}]
    """
    
    try:
        # Send PDF as binary content
        response = model.generate_content([
            prompt,
            {"mime_type": "application/pdf", "data": pdf_content}
        ])
        
        # Parse JSON from response
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif response_text.startswith('```'):
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        products = json.loads(response_text)
        
        if not isinstance(products, list):
            products = []
        
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        products = []
    
    # Create Product objects
    for prod in products:
        Product.objects.create(
            portfolio=portfolio,
            name=prod.get('name', ''),
            description=prod.get('description', ''),
            category=prod.get('category', ''),
            benefits=prod.get('benefits', ''),
            how_to_use=prod.get('how_to_use', ''),
            pdf_ingredients=prod.get('ingredients', '')
        )
    
    return products

def lookup_product_ingredients(products_data):
    """Placeholder for ingredient lookup"""
    return {}

def save_portfolio_as_json(portfolio, products_data, ingredients_lookup=None):
    """Save portfolio data to JSON"""
    pass
