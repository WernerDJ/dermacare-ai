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
                    model="GPT-4.1",
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
        Handles routine queries specially to return diverse products
        """
        
        with trace(f"Agent3: Smart Search - '{query}'"):
            query_lower = query.lower()
            
            # Detect routine queries
            is_routine_query = any(word in query_lower for word in [
                'routine', 'regimen', 'set', 'combo', 'complete', 'full',
                'morning and evening', 'day and night', 'cleanser', 'serum', 'moisturizer'
            ])
            
            # For routines: be more permissive and get more products
            if is_routine_query:
                top_k = 15  # Get 15 instead of 5
                relevance_threshold = 2.5  # More lenient threshold
                self.logger.info(f"🔄 Routine query detected - getting {top_k} diverse products")
            else:
                relevance_threshold = 2.0
            
            # Step 1: Use OpenAI to extract filters
            filters = self.extract_filters_from_query(query)
            
            # For routines, don't filter by treatment_kind (user wants variety)
            if is_routine_query and 'treatment_kind' in filters:
                self.logger.info(f"Routine query: ignoring treatment_kind filter '{filters['treatment_kind']}' for diversity")
                del filters['treatment_kind']
            
            self.logger.info(f"Applied filters: {filters}")
            
            all_results = []
            
            for brand_name in brand_names:
                collection_name = brand_name.lower().replace(" ", "_")
                
                try:
                    collection = self.chroma_client.get_collection(name=collection_name)
                except Exception as e:
                    self.logger.warning(f"Collection not found: {collection_name}")
                    continue
                
                # Vector search
                results = collection.query(
                    query_texts=[query],
                    n_results=top_k * 3  # Get even more to filter
                )
                
                if not results['ids'] or len(results['ids'][0]) == 0:
                    continue
                
                # Filter by metadata constraints
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
            
            # Sort by relevance
            all_results.sort(key=lambda x: x['distance'] if x['distance'] is not None else float('inf'))
            
            # For routines: prefer product type diversity
            if is_routine_query:
                diverse_results = self._select_diverse_products(all_results, top_k)
                self.logger.info(f"Agent3: Returned {len(diverse_results)} diverse products for routine")
                return diverse_results
            else:
                filtered_results = all_results[:top_k]
                self.logger.info(f"Agent3: Returned {len(filtered_results)} products")
                return filtered_results

    def _select_diverse_products(self, all_results: List[Dict], top_k: int) -> List[Dict]:
        """
        For routine queries, select diverse product types instead of just best matches
        Prioritizes: Cleanser, Serum, Moisturizer, SPF
        """
        
        product_types = {}
        
        for result in all_results:
            treatment = result['metadata'].get('treatment_kind', 'Other').lower()
            product_name = result['metadata'].get('product', '').lower()
            
            # Categorize products
            category = 'Other'
            if 'cleanser' in treatment or 'cleanser' in product_name or 'cleansing' in product_name:
                category = 'Cleanser'
            elif 'serum' in treatment or 'serum' in product_name:
                category = 'Serum'
            elif 'moisturizer' in treatment or 'moisturiz' in product_name or 'cream' in product_name:
                category = 'Moisturizer'
            elif 'spf' in product_name or 'sunscreen' in treatment or 'sun protection' in treatment:
                category = 'SPF'
            
            if category not in product_types:
                product_types[category] = []
            product_types[category].append(result)
        
        # Select diverse products: 2 cleansers, 2 serums, 2 moisturizers, 1 SPF
        diverse = []
        selection_strategy = {
            'Cleanser': 2,
            'Serum': 2,
            'Moisturizer': 3,
            'SPF': 1,
            'Other': 2,
        }
        
        for category, count in selection_strategy.items():
            if category in product_types:
                diverse.extend(product_types[category][:count])
        
        return diverse[:top_k]
    

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