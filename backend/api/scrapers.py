"""
Ingredient scrapers for enriching product data
Tries INCIDecoder first, then What's in My Jar
"""

import re
import requests
from bs4 import BeautifulSoup


def slugify(text):
    """Convert product name to URL slug"""
    slug = text.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    return slug


def scrape_incidecoder(product_name):
    """
    Scrape ingredients from INCIDecoder
    Returns: ingredients_string or None
    """
    try:
        slug = slugify(product_name)
        url = f"https://incidecoder.com/products/{slug}"
        
        print(f"📍 Trying INCIDecoder: {url}")
        
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            print(f"⚠️ Product not found on INCIDecoder")
            return None
            
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # INCIDecoder lists ingredients in the main content
        # Look for the ingredient list - usually starts with Aqua/Water
        content_div = soup.find('div', class_='content')
        if not content_div:
            content_div = soup.find('main') or soup.find('article')
        
        if content_div:
            # Get all text from the content area
            text = content_div.get_text()
            
            # Find the ingredient list (comma-separated, typically after product name)
            lines = text.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                # Ingredients typically have many commas and start with Aqua/Water
                if ',' in line and len(line) > 100:
                    if any(term in line for term in ['Aqua', 'Water', 'Alcohol', 'Glycerin']):
                        ingredients = line
                        # Clean up
                        ingredients = ' '.join(ingredients.split())
                        print(f"✅ INCIDecoder found: {ingredients[:100]}...")
                        return ingredients
        
        print(f"⚠️ No ingredients found on INCIDecoder")
        return None
        
    except requests.exceptions.Timeout:
        print(f"⏱️ INCIDecoder timeout")
        return None
    except Exception as e:
        print(f"❌ INCIDecoder error: {str(e)}")
        return None

def scrape_whatsinmyjar(product_name):
    """
    Scrape ingredients from What's in My Jar
    Extracts from the Key Actives section
    Returns: ingredients_string or None
    """
    try:
        slug = slugify(product_name)
        url = f"https://whatsinmyjar.com/product/{slug}"
        
        print(f"📍 Trying What's in My Jar: {url}")
        
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            print(f"⚠️ Product not found on What's in My Jar")
            return None
            
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for ingredient links (they're in <a> tags within the Key Actives section)
        # What's in My Jar uses links like: <a href="/skincare-ingredients/...">Ingredient Name</a>
        
        ingredients = []
        
        # Find all links that point to skincare-ingredients
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text().strip()
            
            # Check if this is an ingredient link
            if '/skincare-ingredients/' in href and text:
                # Skip if text contains numbers or percentages
                if not any(char.isdigit() for char in text):
                    ingredients.append(text)
        
        if ingredients:
            # Join as comma-separated list
            ingredients_str = ', '.join(ingredients)
            print(f"✅ What's in My Jar found {len(ingredients)} ingredients")
            print(f"   {ingredients_str[:100]}...")
            return ingredients_str
        
        print(f"⚠️ No ingredients found")
        return None
        
    except Exception as e:
        print(f"❌ What's in My Jar error: {str(e)}")
        return None


def get_enriched_ingredients(product_name):
    """
    Main function: Try INCIDecoder first, then What's in My Jar
    Returns: (ingredients_string, source) or (None, None)
    """
    print(f"\n🔍 Enriching ingredients for: {product_name}")
    
    # Try INCIDecoder first
    ingredients = scrape_incidecoder(product_name)
    if ingredients:
        return ingredients, 'upc_inci'
    
    # Fall back to What's in My Jar
    ingredients = scrape_whatsinmyjar(product_name)
    if ingredients:
        return ingredients, 'upc_inci'
    
    print(f"⚠️ No enriched ingredients found")
    return None, None