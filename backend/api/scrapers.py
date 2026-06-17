"""
Ingredient scrapers for enriching product data
Tries INCIDecoder first (with and without brand name), then Open Beauty Facts API
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
    Tries with full name first, then without brand name prefix
    Returns: ingredients_string or None
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    # Build list of slugs to try
    slugs_to_try = []

    # Full name slug
    full_slug = slugify(product_name)
    slugs_to_try.append(full_slug)

    # Try without first word (usually the brand name)
    words = product_name.strip().split()
    if len(words) > 1:
        without_brand = ' '.join(words[1:])
        slugs_to_try.append(slugify(without_brand))

    for slug in slugs_to_try:
        try:
            url = f"https://incidecoder.com/products/{slug}"
            print(f"📍 Trying INCIDecoder: {url}")

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 404:
                print(f"⚠️ Not found: {url}")
                continue

            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # INCIDecoder lists ingredients in the main content
            content_div = soup.find('div', class_='content')
            if not content_div:
                content_div = soup.find('main') or soup.find('article')

            if content_div:
                text = content_div.get_text()
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if ',' in line and len(line) > 100:
                        if any(term in line for term in ['Aqua', 'Water', 'Alcohol', 'Glycerin']):
                            ingredients = ' '.join(line.split())
                            print(f"✅ INCIDecoder found: {ingredients[:100]}...")
                            return ingredients

            print(f"⚠️ No ingredients found at: {url}")

        except requests.exceptions.Timeout:
            print(f"⏱ INCIDecoder timeout")
        except Exception as e:
            print(f"❌ INCIDecoder error: {str(e)}")

    return None


def search_open_beauty_facts(product_name):
    """
    Search Open Beauty Facts API for product ingredients
    Returns: ingredients_string or None
    """
    try:
        # Remove brand name (first word) for better search results
        words = product_name.strip().split()
        search_term = ' '.join(words[1:]) if len(words) > 1 else product_name

        url = "https://world.openbeautyfacts.org/cgi/search.pl"
        params = {
            'search_terms': product_name,
            'search_simple': 1,
            'action': 'process',
            'json': 1,
            'page_size': 5,
        }

        print(f"📍 Trying Open Beauty Facts: {product_name}")

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        products = data.get('products', [])
        if not products:
            print(f"⚠️ No results on Open Beauty Facts")
            return None

        # Find best match with ingredients
        for product in products:
            ingredients = product.get('ingredients_text_en') or product.get('ingredients_text', '')
            if ingredients and len(ingredients) > 20:
                print(f"✅ Open Beauty Facts found: {ingredients[:100]}...")
                return ingredients

        print(f"⚠️ Products found but no ingredient data")
        return None

    except requests.exceptions.Timeout:
        print(f"⏱ Open Beauty Facts timeout")
        return None
    except Exception as e:
        print(f"❌ Open Beauty Facts error: {str(e)}")
        return None


def get_enriched_ingredients(product_name):
    """
    Main function: Try INCIDecoder first, then Open Beauty Facts
    Returns: (ingredients_string, source) or (None, None)
    """
    print(f"\n🔍 Enriching ingredients for: {product_name}")

    # Try INCIDecoder first (with improved slug matching)
    ingredients = scrape_incidecoder(product_name)
    if ingredients:
        return ingredients, 'upc_inci'

    # Fall back to Open Beauty Facts API
    ingredients = search_open_beauty_facts(product_name)
    if ingredients:
        return ingredients, 'upc_inci'

    print(f"⚠️ No enriched ingredients found for: {product_name}")
    return None, None
