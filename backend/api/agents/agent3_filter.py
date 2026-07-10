"""
Agent 3: Filter
Searches Chroma database for relevant products based on user query
"""

import logging
from typing import Dict, List
from agents import trace
import chromadb

logger = logging.getLogger(__name__)

class Agent3Filter:
    """
    Filters and retrieves relevant products from Chroma database
    based on user queries
    """
    
    def __init__(self, chroma_db_path: str = "./chroma_db"):
        """Initialize Chroma client"""
        self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        self.db_path = chroma_db_path
        self.logger = logger
    
    def filter_products(self, query: str, brand_names: List[str], top_k: int = 5) -> List[Dict]:
        """
        Filter products with relevance threshold
        """
        
        with trace(f"Agent3: Filter - '{query}'"):
            all_results = []
            relevance_threshold = 2.0  # Only keep results with distance < 2.0
            
            for brand_name in brand_names:
                collection_name = brand_name.lower().replace(" ", "_")
                
                try:
                    collection = self.chroma_client.get_collection(name=collection_name)
                except Exception as e:
                    self.logger.warning(f"Collection not found: {collection_name}")
                    continue
                
                results = collection.query(
                    query_texts=[query],
                    n_results=top_k * 2  # Get more, then filter
                )
                
                if results['ids'] and len(results['ids']) > 0:
                    for i, doc_id in enumerate(results['ids'][0]):
                        distance = results['distances'][0][i] if 'distances' in results else 999
                        
                        # Only include if relevant enough
                        if distance < relevance_threshold:
                            result = {
                                "id": doc_id,
                                "brand": brand_name,
                                "metadata": results['metadatas'][0][i],
                                "distance": distance,
                                "document": results['documents'][0][i] if 'documents' in results else ""
                            }
                            all_results.append(result)
            
            # Sort by relevance and return top_k
            all_results.sort(key=lambda x: x['distance'])
            filtered_results = all_results[:top_k]
            
            self.logger.info(f"Returned {len(filtered_results)} relevant results")
            
            return filtered_results
    
    def format_for_agent4(self, filtered_products: List[Dict]) -> str:
        """
        Format filtered products for Agent 4 (Answerer)
        
        Returns a structured string with product information
        """
        
        if not filtered_products:
            return "No relevant products found."
        
        formatted = "RELEVANT PRODUCTS:\n\n"
        
        for i, product in enumerate(filtered_products, 1):
            metadata = product['metadata']
            formatted += f"{i}. {metadata.get('product', 'Unknown')}\n"
            formatted += f"   Brand: {product['brand']}\n"
            formatted += f"   Type: {metadata.get('treatment_kind', 'N/A')}\n"
            formatted += f"   Skin Type: {metadata.get('skin_type', 'N/A')}\n"
            formatted += f"   Ingredients: {metadata.get('ingredients', 'N/A')}\n"
            formatted += f"   Benefits: {metadata.get('benefits', 'N/A')}\n"
            formatted += f"   Usage: {metadata.get('usage', 'N/A')}\n\n"
        
        return formatted
    
    def get_available_brands(self) -> List[str]:
        """Get list of available brands in the database"""
        
        collections = self.chroma_client.list_collections()
        brands = [col.name.replace("_", " ").title() for col in collections]
        
        return brands