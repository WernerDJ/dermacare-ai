"""
Agent 3: Smart Filter with OpenAI-Powered Analysis
Uses AI to extract metadata filters from user queries
"""
import logging
from typing import Dict, List, Optional
from agents import trace
import chromadb
import json
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

class Agent3Filter:
    """
    Filters and retrieves relevant products using AI-powered filter extraction
    """
    
    # Correct life stage hierarchy
    LIFE_STAGE_HIERARCHY = {
        'all ages': ['all ages', 'babies', 'children', 'teenagers', 'adults', 'menopausal', 'post-menopausal'],
        'babies': ['babies'],
        'children': ['children', 'teenagers', 'adults'],  # Children can use teen+ products
        'teenagers': ['teenagers', 'adults', 'menopausal', 'post-menopausal'],
        'adults': ['adults', 'menopausal', 'post-menopausal'],
        'menopausal': ['menopausal', 'post-menopausal'],
        'post-menopausal': ['post-menopausal'],
    }
    
    def __init__(self, chroma_db_path: str = "./chroma_db", openai_api_key: Optional[str] = None):
        """Initialize Chroma client and OpenAI"""
        self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        self.db_path = chroma_db_path
        self.logger = logger
        
        # Initialize OpenAI
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=api_key)
    
    def extract_filters_from_query(self, query: str) -> Dict:
        """
        Use OpenAI to intelligently extract metadata filters from user query
        
        Returns:
            Dict with keys: gender, skin_type, life_stage, treatment_kind
        """
        
        extraction_prompt = f"""Analyze this skincare question and extract relevant filters.

Question: "{query}"

Available filter options:
- Gender: male, female, unisex (or null if not specified)
- Skin Type: oily, dry, sensitive, combination, all (or null if not specified)
- Life Stage: babies, children, teenagers, adults, menopausal, post-menopausal, all ages (or null if not specified)
- Treatment Kind: acne, anti-aging, rosacea, hyperpigmentation, eczema, psoriasis, hydration, brightening, firming, sun protection (or any other specific concern mentioned)

Respond ONLY with valid JSON, no other text:
{{
    "gender": "value or null",
    "skin_type": "value or null",
    "life_stage": "value or null",
    "treatment_kind": "value or null",
    "reasoning": "Brief explanation of what you extracted"
}}"""
        
        try:
            with trace("Agent3: OpenAI Filter Extraction"):
                response = self.openai_client.messages.create(
                    model="gpt-4o-mini",
                    max_tokens=500,
                    messages=[
                        {"role": "user", "content": extraction_prompt}
                    ]
                )
                
                response_text = response.content[0].text
                
                # Parse JSON response
                try:
                    filters = json.loads(response_text)
                    
                    # Clean up null values
                    filters = {k: v for k, v in filters.items() if v is not None and k != "reasoning"}
                    
                    self.logger.info(f"OpenAI extracted filters: {filters}")
                    self.logger.info(f"Reasoning: {response_text.get('reasoning', 'N/A')}")
                    
                    return filters
                except json.JSONDecodeError:
                    self.logger.error(f"Failed to parse OpenAI response: {response_text}")
                    return {}
                    
        except Exception as e:
            self.logger.error(f"OpenAI filter extraction failed: {str(e)}")
            return {}
    
    def search_products(self, query: str, brand_names: List[str], top_k: int = 5) -> List[Dict]:
        """
        Search products using metadata filtering + semantic search
        
        Args:
            query: User's question/search query
            brand_names: List of brands to search in
            top_k: Number of top results to return
            
        Returns:
            List of relevant products with metadata
        """
        
        with trace(f"Agent3: Smart Search - '{query}'"):
            # Step 1: Use OpenAI to extract filters
            filters = self.extract_filters_from_query(query)
            self.logger.info(f"Applied filters: {filters}")
            
            all_results = []
            relevance_threshold = 2.0
            
            for brand_name in brand_names:
                collection_name = brand_name.lower().replace(" ", "_")
                
                try:
                    collection = self.chroma_client.get_collection(name=collection_name)
                except Exception as e:
                    self.logger.warning(f"Collection not found: {collection_name}")
                    continue
                
                # Step 2: Vector search
                results = collection.query(
                    query_texts=[query],
                    n_results=top_k * 5
                )
                
                if not results['ids'] or len(results['ids'][0]) == 0:
                    continue
                
                # Step 3: Filter by metadata constraints
                for i, doc_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i] if 'distances' in results else 999
                    metadata = results['metadatas'][0][i]
                    
                    if distance >= relevance_threshold:
                        continue
                    
                    if not self._matches_filters(metadata, filters):
                        continue
                    
                    result = {
                        "id": doc_id,
                        "brand": brand_name,
                        "metadata": metadata,
                        "distance": distance,
                        "document": results['documents'][0][i] if 'documents' in results else ""
                    }
                    all_results.append(result)
            
            # Step 4: Sort by relevance and return top_k
            all_results.sort(key=lambda x: x['distance'] if x['distance'] is not None else float('inf'))
            filtered_results = all_results[:top_k]
            
            self.logger.info(f"Agent3: Returned {len(filtered_results)} products")
            
            return filtered_results
    
    def _matches_filters(self, product_metadata: Dict, filters: Dict) -> bool:
        """
        Check if product metadata matches all extracted filters
        """
        
        # Gender filter
        if 'gender' in filters:
            product_gender = product_metadata.get('gender', 'unisex').lower()
            if product_gender not in ['unisex', filters['gender'].lower()]:
                return False
        
        # Skin type filter
        if 'skin_type' in filters:
            product_skin = product_metadata.get('skin_type', 'all').lower()
            if product_skin != 'all' and product_skin != filters['skin_type'].lower():
                return False
        
        # Life stage filter (hierarchical)
        if 'life_stage' in filters:
            product_life_stage = product_metadata.get('life_stage', 'all ages').lower()
            
            if product_life_stage != 'all ages':
                user_life_stage = filters['life_stage'].lower()
                allowed_stages = self.LIFE_STAGE_HIERARCHY.get(user_life_stage, [user_life_stage])
                
                if product_life_stage not in allowed_stages:
                    return False
        
        # Treatment kind filter
        if 'treatment_kind' in filters:
            product_treatment = product_metadata.get('treatment_kind', '').lower()
            
            if product_treatment:
                if product_treatment != filters['treatment_kind'].lower():
                    return False
        
        return True
    
    def format_for_agent4(self, filtered_products: List[Dict]) -> str:
        """
        Format filtered products for Agent 4 (Answerer)
        """
        
        if not filtered_products:
            return "No relevant products found matching your criteria."
        
        formatted = "RELEVANT PRODUCTS:\n\n"
        
        for i, product in enumerate(filtered_products, 1):
            metadata = product['metadata']
            formatted += f"{i}. {metadata.get('product', 'Unknown')}\n"
            formatted += f"   Brand: {product['brand']}\n"
            formatted += f"   For: {metadata.get('gender', 'Unisex')} | Age Group: {metadata.get('life_stage', 'All ages')} | Skin Type: {metadata.get('skin_type', 'All')}\n"
            formatted += f"   Concern: {metadata.get('treatment_kind', 'General Care')}\n"
            formatted += f"   Benefits: {metadata.get('benefits', 'N/A')}\n"
            formatted += f"   How to Use: {metadata.get('usage', 'N/A')}\n"
            formatted += f"   Relevance: {1 - product['distance']:.2f}/1.0\n\n"
        
        return formatted
    
    def get_available_brands(self) -> List[str]:
        """Get list of available brands"""
        
        collections = self.chroma_client.list_collections()
        brands = [col.name.replace("_", " ").title() for col in collections]
        
        return brands
    
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