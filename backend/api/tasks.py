from celery import shared_task
from django.utils import timezone
import json
import os
from pathlib import Path
from .models import BrandPortfolio, Product, Ingredient, AnalysisTask
from .agents import Agent1Extractor, Agent2Vectorizer
from django.conf import settings

@shared_task(bind=True)
def analyze_portfolio_task(self, portfolio_id, pdf_path, lookup_ingredients=True):
    """Analyze portfolio using Agent 1 + Agent 2"""
    
    portfolio = BrandPortfolio.objects.get(id=portfolio_id)
    
    try:
        # AGENT 1: Extract products
        print(f"🔍 Agent 1: Extracting from {Path(pdf_path).name}")
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        extractor = Agent1Extractor(api_key=openai_api_key)
        
        products, errors = extractor.extract_from_document(
            file_path=pdf_path,
            brand_name=portfolio.name
        )
        
        print(f"✅ Extracted {len(products)} products, {len(errors)} errors")
        
        # Report errors if any
        if errors:
            error_report = extractor.generate_error_report(errors)
            print(f"⚠️ Extraction Report:\n{error_report}")
        
        # AGENT 2: Vectorize and store
        print(f"🧠 Agent 2: Vectorizing products")
        
        vectorizer = Agent2Vectorizer(chroma_db_path="/app/chroma_db")
        
        stored_count, enrichment_log = vectorizer.vectorize_products(
            products=products,
            brand_name=portfolio.name
        )
        
        print(f"✅ Stored {stored_count} products in Chroma")
        
        # Count enrichments
        enriched_count = sum(1 for log in enrichment_log if log.get('enriched'))
        print(f"✅ Enriched {enriched_count}/{len(products)} products")
        
        # Update task status
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.product_count = stored_count
        task.save()
        
        return {
            'status': 'success',
            'portfolio_id': portfolio_id,
            'products': stored_count,
            'enriched': enriched_count,
            'errors': len(errors)
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        task.status = 'failed'
        task.error_message = str(e)
        task.save()
        
        return {
            'status': 'error',
            'portfolio_id': portfolio_id,
            'error': str(e)
        }
    # After vectorizer.vectorize_products() completes
    # Create Django Product objects for the database

    for idx, product in enumerate(products):
        try:
            Product.objects.create(
                portfolio=portfolio,
                name=product['product'],
                description=product['benefits'] or '',
                category=product['treatment_kind'] or 'General',
                benefits=product['benefits'] or '',
                how_to_use=product['usage'] or '',
                pdf_ingredients=product.get('ingredients_enriched', product['ingredients'])
            )
        except Exception as e:
            logger.warning(f"Error creating Product object: {str(e)}")