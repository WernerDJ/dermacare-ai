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

openai_api_key = os.getenv("OPENAI_API_KEY")
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
    
    def vectorize_products(self, products: List[Dict], brand_name: str) -> Tuple[int, List[Dict]]:
        """
        Vectorize and store products in Chroma
        
        Args:
            products: List of products from Agent 1
            brand_name: Brand name (for collection naming)
            
        Returns:
            (products_stored, enrichment_log)
        """
        
        enrichment_log = []
        
        # Create or get collection
        collection_name = brand_name.lower().replace(" ", "_")
        collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"brand": brand_name}
        )
        
        self.logger.info(f"Using collection: {collection_name}")
        
        # Process each product
        for idx, product in enumerate(products):
            with trace(f"Process: {product['product']}"):
                # Check if ingredients need enrichment
                ingredient_count = len(product['ingredients'].split(','))
                
                if ingredient_count < 7:
                    # Enrich ingredients
                    enriched, source = self._enrich_ingredients(product, openai_api_key)
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
                    "usage": product['usage'],
                    "benefits": product['benefits']
                }
                
                # Create searchable text
                searchable_text = self._create_searchable_text(product)
                
                # Store in Chroma
                collection.add(
                    ids=[doc_id],
                    documents=[searchable_text],
                    metadatas=[metadata]
                )
                
                self.logger.info(f"Stored: {product['product']}")
        
        return len(products), enrichment_log

    def _enrich_ingredients(self, product: Dict, openai_api_key: str = None) -> Tuple[str, str]:
        """Enrich ingredients using scrapers"""
        
        try:
            import os
            if not openai_api_key:
                openai_api_key = os.getenv("OPENAI_API_KEY")
            
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