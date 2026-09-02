"""
Agent 3.5: Ingredient Enricher
Enriches queries with chemical compound synonyms from PubChem
"""
import logging
import requests
from typing import List, Dict
import re

logger = logging.getLogger(__name__)

class Agent35Enricher:
    """
    Detects chemical compounds in queries and expands with synonyms from PubChem
    """
    
    def __init__(self):
        self.pubchem_base = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        self.cache = {}
    
    def extract_ingredients_from_query(self, query: str) -> List[str]:
        """
        Extract potential chemical compounds from query
        Uses keywords like "contains", "without", "includes", etc.
        """
        
        # Look for patterns like "without X", "contains Y", "has Z"
        patterns = [
            r'without\s+([a-zA-Z\s\-]+?)(?:\s+and|\s+or|$)',
            r'contains?\s+([a-zA-Z\s\-]+?)(?:\s+and|\s+or|$)',
            r'includes?\s+([a-zA-Z\s\-]+?)(?:\s+and|\s+or|$)',
            r'ingredients?.*?([a-zA-Z\s\-]+?)(?:\s+and|\s+or|$)',
        ]
        
        ingredients = []
        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            ingredients.extend(matches)
        
        # Clean up and deduplicate
        cleaned = []
        for ing in ingredients:
            ing = ing.strip()
            if len(ing) > 2 and ing.lower() not in [c.lower() for c in cleaned]:
                cleaned.append(ing)
        
        return cleaned[:5]  # Limit to 5 ingredients to avoid too many API calls
    
    def get_pubchem_synonyms(self, compound_name: str) -> List[str]:
        """
        Query PubChem for compound synonyms
        Returns empty list if not found
        """
        
        # Check cache first
        cache_key = compound_name.lower()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Search for compound
            search_url = f"{self.pubchem_base}/compound/name/{compound_name}/json"
            response = requests.get(search_url, timeout=5)
            
            if response.status_code != 200:
                logger.warning(f"PubChem search failed for '{compound_name}': {response.status_code}")
                return []
            
            data = response.json()
            
            if 'PC_Compounds' not in data or len(data['PC_Compounds']) == 0:
                logger.info(f"No PubChem results for '{compound_name}'")
                return []
            
            # Get CID (Compound ID)
            cid = data['PC_Compounds'][0]['id']['id']['cid']
            
            # Get synonyms
            synonyms_url = f"{self.pubchem_base}/compound/cid/{cid}/synonyms/json"
            syn_response = requests.get(synonyms_url, timeout=5)
            
            if syn_response.status_code != 200:
                return [compound_name]
            
            syn_data = syn_response.json()
            synonyms = []
            
            if 'InformationList' in syn_data:
                for info in syn_data['InformationList']['Information']:
                    if 'Synonym' in info:
                        synonyms.extend(info['Synonym'][:10])  # Limit to 10 per compound
            
            # Cache result
            result = list(set([compound_name] + synonyms))[:15]  # Max 15 synonyms
            self.cache[cache_key] = result
            
            logger.info(f"Found {len(result)} synonyms for '{compound_name}'")
            return result
            
        except Exception as e:
            logger.error(f"PubChem lookup failed for '{compound_name}': {str(e)}")
            return [compound_name]
    
    def enrich_query(self, query: str) -> str:
        """
        Main method: Extract ingredients and expand query with synonyms
        """
        
        ingredients = self.extract_ingredients_from_query(query)
        
        if not ingredients:
            return query
        
        logger.info(f"Extracted ingredients: {ingredients}")
        
        enriched = query
        
        for ingredient in ingredients:
            synonyms = self.get_pubchem_synonyms(ingredient)
            
            if len(synonyms) > 1:
                # Add synonyms to query with OR
                syn_query = " OR ".join(synonyms[1:])  # Skip original
                enriched += f" OR {syn_query}"
                logger.info(f"Added {len(synonyms)-1} synonyms for '{ingredient}'")
        
        return enriched


    def extract_excluded_ingredients(self, query: str) -> Dict[str, List[str]]:
	    """
	    Extract ingredients that should be EXCLUDED from results
	    Returns dict: {'avobenzone': ['Butyl methoxydibenzoylmethane', 'Avobenzonum', ...]}
	    """
	    
	    # Patterns for exclusion: "without X", "no X", "avoids X", "free from X"
	    exclude_patterns = [
	        r'without\s+([a-zA-Z\s\-]+?)(?:\s+and|\s+or|,|$)',
	        r'no\s+([a-zA-Z\s\-]+?)(?:\s+and|\s+or|,|$)',
	        r'avoids?\s+([a-zA-Z\s\-]+?)(?:\s+and|\s+or|,|$)',
	        r'free\s+from\s+([a-zA-Z\s\-]+?)(?:\s+and|\s+or|,|$)',
	    ]
	    
	    excluded = {}
	    
	    for pattern in exclude_patterns:
	        matches = re.findall(pattern, query, re.IGNORECASE)
	        for ingredient in matches:
	            ingredient = ingredient.strip()
	            if len(ingredient) > 2:
	                # Get all synonyms for this ingredient
	                synonyms = self.get_pubchem_synonyms(ingredient)
	                if ingredient.lower() not in excluded:
	                    excluded[ingredient.lower()] = synonyms
	    
	    logger.info(f"Excluded ingredients: {excluded}")
	    return excluded

	def filter_products_by_excluded_ingredients(self, products: List[Dict], excluded_ingredients: Dict[str, List[str]]) -> List[Dict]:
	    """
	    Filter out products that contain any of the excluded ingredients
	    """
	    
	    if not excluded_ingredients:
	        return products
	    
	    filtered = []
	    
	    for product in products:
	        ingredients_str = product['metadata'].get('ingredients', '').lower()
	        benefits_str = product['metadata'].get('benefits', '').lower()
	        
	        # Check if any excluded ingredient or its synonyms are in the product
	        should_exclude = False
	        for ingredient, synonyms in excluded_ingredients.items():
	            for synonym in synonyms:
	                if synonym.lower() in ingredients_str or synonym.lower() in benefits_str:
	                    logger.info(f"Excluding {product['metadata'].get('product')} - contains {synonym}")
	                    should_exclude = True
	                    break
	            if should_exclude:
	                break
	        
	        if not should_exclude:
	            filtered.append(product)
	    
	    logger.info(f"Filtered {len(products)} → {len(filtered)} products (excluded {len(products) - len(filtered)})")
	    return filtered