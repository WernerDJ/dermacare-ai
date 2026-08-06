from django.core.management.base import BaseCommand, CommandError
from api.models import Product, BrandPortfolio
from openai import OpenAI
import os
import time

class Command(BaseCommand):
    help = 'Translate product benefits and usage from Spanish to English'
    
    def add_arguments(self, parser):
        parser.add_argument('--brand', type=str, required=True, help='Brand name to translate')
    
    def handle(self, *args, **options):
        brand_name = options['brand']
        
        try:
            portfolio = BrandPortfolio.objects.get(name=brand_name)
        except BrandPortfolio.DoesNotExist:
            raise CommandError(f"Brand '{brand_name}' not found")
        
        products = Product.objects.filter(portfolio=portfolio)
        product_count = products.count()
        
        if product_count == 0:
            raise CommandError(f"No products found for '{brand_name}'")
        
        self.stdout.write(f"🔄 Translating {product_count} {brand_name} products from Spanish to English...\n")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise CommandError("OPENAI_API_KEY environment variable not set")
        
        client = OpenAI(api_key=api_key)
        
        translated_count = 0
        failed_count = 0
        
        for i, p in enumerate(products, 1):
            self.stdout.write(f"{i}/{product_count}. Translating {p.name}...", ending=" ")
            
            try:
                text_to_translate = f"Benefits:\n{p.benefits}\n\nUsage:\n{p.how_to_use}"
                
                # Use client.chat.completions.create() instead of client.messages.create()
                response = client.chat.completions.create(
                    model="gpt-4.1",
                    max_tokens=500,
                    messages=[{
                        "role": "user",
                        "content": f"Translate from Spanish to English, keep the format:\n\n{text_to_translate}"
                    }]
                )
                
                translation = response.choices[0].message.content
                
                # Parse response
                lines = translation.split('\n')
                benefits_start = None
                usage_start = None
                
                for idx, line in enumerate(lines):
                    if 'Benefits' in line or 'benefits' in line:
                        benefits_start = idx + 1
                    elif 'Usage' in line or 'usage' in line:
                        usage_start = idx + 1
                
                if benefits_start is not None:
                    if usage_start is not None:
                        new_benefits = '\n'.join(lines[benefits_start:usage_start-1]).strip()
                        new_usage = '\n'.join(lines[usage_start:]).strip()
                    else:
                        new_benefits = '\n'.join(lines[benefits_start:]).strip()
                        new_usage = p.how_to_use
                else:
                    new_benefits = translation
                    new_usage = p.how_to_use
                
                p.benefits = new_benefits
                p.how_to_use = new_usage
                p.save()
                
                self.stdout.write(self.style.SUCCESS("✅"))
                translated_count += 1
                time.sleep(1)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ {str(e)}"))
                failed_count += 1
                time.sleep(2)
        
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(self.style.SUCCESS(f"✅ Translation complete!"))
        self.stdout.write(f"Translated: {translated_count}/{product_count}")
        if failed_count > 0:
            self.stdout.write(self.style.WARNING(f"Failed: {failed_count}"))
        
        # Re-vectorize
        self.stdout.write(f"\n🔄 Re-vectorizing to ChromaDB...")
        
        from api.agents import Agent2Vectorizer
        
        products = Product.objects.filter(portfolio=portfolio)
        products_list = [
            {
                'product': p.name,
                'brand': portfolio.name,
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
            for p in products
        ]
        
        try:
            vectorizer = Agent2Vectorizer(chroma_db_path="/app/chroma_db")
            stored_count, _ = vectorizer.vectorize_products(products_list, portfolio.name)
            self.stdout.write(self.style.SUCCESS(f"✅ Re-vectorized {stored_count} products!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Re-vectorization failed: {str(e)}"))
