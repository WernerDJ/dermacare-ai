"""
Agent 2: Vectorizer
Takes products from Agent 1, enriches ingredients, creates vector embeddings
"""
import os
import json
import logging
from typing import Dict, List, Tuple
from agents import trace
import chromadb
from api.scrapers import get_enriched_ingredients

logger = logging.getLogger(__name__)

class Agent2Vectorizer:
    """
    Vectorizes products and stores in Chroma database
    
    Process:
    1. Take products from Agent 1
    2. Enrich ingredients (if < 7, call scrapers)
    3. Create metadata embeddings
    4. Store in Chroma database
    """
    
    def __init__(self, chroma_db_path: str = "./chroma_db"):
        """Initialize Chroma client and embedding model"""
        self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        self.db_path = chroma_db_path
        self.logger = logger
        self.openai_api_key = os.getenv("OPENAI_API_KEY")


    def vectorize_products(self, products: List[Dict], brand_name: str) -> Tuple[int, List[Dict]]:
        """Vectorize and store products in Chroma AND Django database"""
        from api.models import Product  # Import at top of method
        
        enrichment_log = []
        
        collection_name = brand_name.lower().replace(" ", "_")
        collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"brand": brand_name}
        )
        
        self.logger.info(f"Using collection: {collection_name}")
        
        for idx, product in enumerate(products):
            with trace(f"Process: {product['product']}"):
                # Check if ingredients need enrichment
                ingredient_count = len(product['ingredients'].split(','))
                
                if ingredient_count < 7:
                    enriched, source = self._enrich_ingredients(product)
                    if enriched:
                        product['ingredients_enriched'] = enriched
                        product['ingredients_source'] = source
                        enrichment_log.append({
                            "product": product['product'],
                            "enriched": True,
                            "source": source
                        })
                    else:
                        enrichment_log.append({
                            "product": product['product'],
                            "enriched": False,
                            "reason": "No enrichment found"
                        })
                else:
                    enrichment_log.append({
                        "product": product['product'],
                        "enriched": False,
                        "reason": "Enough ingredients already"
                    })
                
                # Create document for storage
                doc_id = f"{brand_name}_{idx}_{product['product'].replace(' ', '_')}"
                metadata = {
                    "brand": product['brand'],
                    "product": product['product'],
                    "skin_type": product['skin_type'],
                    "treatment_kind": product['treatment_kind'],
                    "skin_problems": json.dumps(product['skin_problems']),
                    "body_parts": json.dumps(product['body_parts']),
                    "life_stage": product.get('life_stage', 'Unknown'),
                    "gender": product.get('gender', 'Unknown'),
                    "ingredients": product.get('ingredients_enriched', product['ingredients']),
                    "usage": product['usage'],
                    "benefits": product['benefits']
                }
                
                # Create searchable text (includes new fields)
                searchable_text = self._create_searchable_text(product)
                
                # Store in Chroma
                collection.add(
                    ids=[doc_id],
                    documents=[searchable_text],
                    metadatas=[metadata]
                )
                
                self.logger.info(f"Stored: {product['product']}")
        
        # ✅ NEW: Save products to Django database AFTER Chroma storage
        from django.utils import timezone
        portfolio = None
        
        try:
            from api.models import BrandPortfolio
            portfolio = BrandPortfolio.objects.get(name=brand_name)
            
            for product in products:
                Product.objects.create(
                    portfolio=portfolio,
                    name=product.get('product', 'Unknown'),
                    description=product.get('benefits', ''),
                    category=product.get('treatment_kind', ''),
                    benefits=product.get('benefits', ''),
                    how_to_use=product.get('usage', ''),
                    pdf_ingredients=product.get('ingredients_enriched', product.get('ingredients', '')),
                    skin_type=product.get('skin_type', 'all'),
                    treatment_kind=product.get('treatment_kind', ''),
                    life_stage=product.get('life_stage', 'all'),
                    gender=product.get('gender', 'unisex'),
                )
            
            self.logger.info(f"✅ Saved {len(products)} products to database")
        except Exception as e:
            self.logger.error(f"❌ Error saving to database: {str(e)}")
        
        return len(products), enrichment_log




    def _create_searchable_text(self, product: Dict) -> str:
        """Create searchable text from product metadata"""
        
        parts = [
            product['product'],
            product['skin_type'],
            product['treatment_kind'],
            ', '.join(product['skin_problems']),
            ', '.join(product['body_parts']),
            product.get('life_stage', 'Unknown'),
            product.get('gender', 'Unknown'),
            product['ingredients'],
            product['benefits'],
            product['usage']
        ]
        
        return ' | '.join(parts)

    def _enrich_ingredients(self, product: Dict) -> Tuple[str, str]:
        """Enrich ingredients using scrapers"""
        
        try:
            openai_api_key = self.openai_api_key
            
            enriched, source = get_enriched_ingredients(
                f"{product['brand']} {product['product']}",
                openai_api_key=openai_api_key
            )
            
            if enriched:
                combined = f"{product['ingredients']}, {enriched}"
                return combined, source
            
            return None, None
            
        except Exception as e:
            self.logger.warning(f"Enrichment failed: {str(e)}")
            return None, None

    
    def _create_searchable_text(self, product: Dict) -> str:
        """Create searchable text from product metadata"""
        
        parts = [
            product['product'],
            product['skin_type'],
            product['treatment_kind'],
            ', '.join(product['skin_problems']),
            ', '.join(product['body_parts']),
            product['ingredients'],
            product['benefits'],
            product['usage']
        ]
        
        return ' | '.join(parts)
    
    def search_products(self, brand_name: str, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search products in Chroma database
        
        Args:
            brand_name: Brand to search in
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of matching products
        """
        
        with trace(f"Agent2: Search {brand_name}"):
            collection_name = brand_name.lower().replace(" ", "_")
            
            try:
                collection = self.chroma_client.get_collection(name=collection_name)
            except Exception as e:
                self.logger.error(f"Collection not found: {collection_name}")
                return []
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            products = []
            if results['ids'] and len(results['ids']) > 0:
                for i, doc_id in enumerate(results['ids'][0]):
                    product = {
                        "id": doc_id,
                        "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None
                    }
                    products.append(product)
            
            return products
    
    def get_collection_stats(self, brand_name: str) -> Dict:
        """Get stats about a collection"""
        
        collection_name = brand_name.lower().replace(" ", "_")
        
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            count = collection.count()
            
            return {
                "collection": collection_name,
                "total_products": count,
                "status": "ready"
            }
        except Exception as e:
            return {
                "collection": collection_name,
                "status": "not_found",
                "error": str(e)
            }

    def re_vectorize_product(self, product_dict: Dict, brand_name: str, product_index: int) -> bool:
        """Re-vectorize a single product (for admin ingredient edits)"""
        
        with trace(f"Agent2: Re-vectorize - {product_dict['product']}"):
            try:
                collection_name = brand_name.lower().replace(" ", "_")
                collection = self.chroma_client.get_or_create_collection(
                    name=collection_name,
                    metadata={"brand": brand_name}
                )
                
                doc_id = f"{brand_name}_{product_index}_{product_dict['product'].replace(' ', '_')}"
                metadata = {
                    "brand": product_dict['brand'],
                    "product": product_dict['product'],
                    "skin_type": product_dict['skin_type'],
                    "treatment_kind": product_dict['treatment_kind'],
                    "skin_problems": json.dumps(product_dict.get('skin_problems', [])),
                    "body_parts": json.dumps(product_dict.get('body_parts', ['Face'])),
                    "life_stage": product_dict.get('life_stage', 'Unknown'),
                    "gender": product_dict.get('gender', 'Unknown'),
                    "ingredients": product_dict['ingredients'],
                    "usage": product_dict['usage'],
                    "benefits": product_dict['benefits']
                }
                
                searchable_text = self._create_searchable_text(product_dict)
                
                try:
                    collection.delete(ids=[doc_id])
                except:
                    pass
                
                collection.add(
                    ids=[doc_id],
                    documents=[searchable_text],
                    metadatas=[metadata]
                )
                
                self.logger.info(f"Re-vectorized: {product_dict['product']}")
                return True
                
            except Exception as e:
                self.logger.error(f"Re-vectorization failed: {str(e)}")
                return False