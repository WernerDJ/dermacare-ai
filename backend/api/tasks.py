from celery import shared_task
from django.utils import timezone
import os
from pathlib import Path
from .models import BrandPortfolio, Product, AnalysisTask
from .agents import Agent1Extractor, Agent2Vectorizer

@shared_task(bind=True)
def analyze_portfolio_task(self, portfolio_id, document_path, brand_name, product_names, lookup_ingredients=True):
    """Analyze portfolio using Agent 1 with manual product list"""
    
    portfolio = BrandPortfolio.objects.get(id=portfolio_id)
    
    try:
        # AGENT 1: Extract products by name
        print(f"🔍 Agent 1: Extracting {len(product_names)} products from {Path(document_path).name}")
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        extractor = Agent1Extractor(api_key=openai_api_key)
        
        products, errors = extractor.extract_from_document(
            file_path=document_path,
            brand_name=brand_name,
            product_names=product_names
        )
        
        print(f"✅ Extracted {len(products)} products, {len(errors)} errors")
        
        if errors:
            error_report = extractor.generate_error_report(errors)
            print(f"⚠️ Failed to extract:\n{error_report}")
        
        # AGENT 2: Vectorize
        print(f"🧠 Agent 2: Vectorizing products")
        
        vectorizer = Agent2Vectorizer(chroma_db_path="/app/chroma_db")
        stored_count, enrichment_log = vectorizer.vectorize_products(
            products=products,
            brand_name=brand_name
        )
        
        print(f"✅ Stored {stored_count} products in Chroma")
        
        enriched_count = sum(1 for log in enrichment_log if log.get('enriched'))
        print(f"✅ Enriched {enriched_count}/{len(products)} products")
        
        # Create Django Product objects
        for product in products:
            try:
                Product.objects.create(
                    portfolio=portfolio,
                    name=product['product'],
                    description=product['benefits'] or '',
                    category=product['treatment_kind'] or 'General',
                    benefits=product['benefits'] or '',
                    how_to_use=product['usage'] or '',
                    pdf_ingredients=product.get('ingredients', 'Unknown'),
                    life_stage=product.get('life_stage', 'Unknown').lower(),
                    gender=product.get('gender', 'Unknown').lower(),
                )
            except Exception as e:
                print(f"Error creating Product: {str(e)}")
        
        # Check how many products were actually saved to database
        final_db_count = Product.objects.filter(portfolio=portfolio).count()
        print(f"✅ Products saved to database: {final_db_count}")
        
        # Always re-vectorize to ensure ChromaDB is in sync with database
        if final_db_count > 0:
            print(f"🔄 Auto-syncing ChromaDB with database...")
            try:
                # Get all products from database
                db_products = Product.objects.filter(portfolio=portfolio)
                products_to_sync = [
                    {
                        'product': p.name,
                        'brand': brand_name,
                        'skin_type': p.skin_type,
                        'treatment_kind': p.treatment_kind,
                        'skin_problems': [],
                        'body_parts': ['Face'],
                        'life_stage': p.life_stage,
                        'gender': p.gender,
                        'ingredients': p.pdf_ingredients,
                        'usage': p.how_to_use,
                        'benefits': p.benefits,
                    }
                    for p in db_products
                ]
                
                # Re-vectorize everything
                vectorizer = Agent2Vectorizer(chroma_db_path="/app/chroma_db")
                synced_count, _ = vectorizer.vectorize_products(products_to_sync, brand_name)
                
                print(f"✅ ChromaDB synced: {synced_count} products")
                
            except Exception as e:
                print(f"⚠️ ChromaDB sync failed: {str(e)}")
        
        # Update portfolio count with actual database count
        portfolio.total_products = final_db_count
        portfolio.save()
        print(f"✅ Portfolio updated: {final_db_count} products")
        
        # Update task
        analysis_task = AnalysisTask.objects.get(task_id=self.request.id)
        analysis_task.status = 'completed'
        analysis_task.completed_at = timezone.now()
        analysis_task.product_count = final_db_count
        analysis_task.save()
        
        return {
            'status': 'success',
            'portfolio_id': portfolio_id,
            'products_found': final_db_count,
            'products_failed': len(errors),
            'enriched': enriched_count,
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        analysis_task = AnalysisTask.objects.get(task_id=self.request.id)
        analysis_task.status = 'failed'
        analysis_task.error_message = str(e)
        analysis_task.save()
        
        return {
            'status': 'error',
            'portfolio_id': portfolio_id,
            'error': str(e)
        }