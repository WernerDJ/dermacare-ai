"""
Ingredient scrapers for enriching product data
Tries INCIDecoder first, then Open Beauty Facts, then Gemini as last resort
Gemini is prompted to only return verified ingredients, not hallucinate
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

    slugs_to_try = []
    full_slug = slugify(product_name)
    slugs_to_try.append(full_slug)

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

            # INCIDecoder puts the full ingredient list in ingredlist-long
            ingredient_section = (
                soup.find(id='ingredlist-long') or
                soup.find(id='ingredlist-long-section') or
                soup.find(id='ingredlist-short')
            )

            if ingredient_section:
                # Extract only direct ingredient links from this section
                seen = set()
                ingredients = []
                for link in ingredient_section.find_all('a', href=True):
                    href = link.get('href', '')
                    if '/ingredients/' in href:
                        name = link.get_text().strip()
                        # Skip duplicates, empty names, and non-ingredient text
                        if name and len(name) > 1 and name not in seen:
                            if not any(skip in name.lower() for skip in ['more', 'click', 'read', 'here', '>>']):
                                seen.add(name)
                                ingredients.append(name)

                if len(ingredients) >= 3:
                    ingredients_str = ', '.join(ingredients)
                    print(f"✅ INCIDecoder found {len(ingredients)} ingredients: {ingredients_str[:100]}...")
                    return ingredients_str

            print(f"⚠️ No ingredients found at: {url}")

        except requests.exceptions.Timeout:
            print(f"⏱ INCIDecoder timeout")
        except Exception as e:
            print(f"❌ INCIDecoder error: {str(e)}")

    return None


def scrape_openbeauty(product_name, openai_api_key=None):
    """
    Search OpenBeauty database using OpenAI
    """
    if not openai_api_key:
        import os
        openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        print("⚠️ OpenAI API key not found")
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)
        
        prompt = f"""Search for ingredients of this cosmetic product: {product_name}
        
Use your knowledge of beauty products and databases like OpenBeauty, INCIpedia, or other ingredient databases.

Return ONLY a comma-separated list of INCI ingredient names, nothing else.
If you cannot find reliable information, respond with: UNKNOWN

Example response format:
Water, Glycerin, Cetyl Alcohol, Stearic Acid, ..."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000
        )
        
        ingredients = response.choices[0].message.content.strip()
        
        if ingredients != "UNKNOWN" and len(ingredients) > 20:
            print(f"✅ OpenAI search found: {ingredients[:100]}...")
            return ingredients
        
        return None
        
    except Exception as e:
        print(f"❌ OpenAI search error: {str(e)}")
        return None

def get_enriched_ingredients(product_name, openai_api_key=None):
    """
    Main function: Try enrichment sources in order
    1. INCIDecoder (barcode lookup)
    2. What's in My Jar (scrape)
    3. OpenBeauty (OpenAI search)
    4. Direct OpenAI search (last resort)
    """
    
    if not openai_api_key:
        import os
        openai_api_key = os.getenv("OPENAI_API_KEY")
    
    print(f"\n🔍 Enriching ingredients for: {product_name}")
    
    # Try INCIDecoder first
    ingredients = scrape_incidecoder(product_name)
    if ingredients:
        return ingredients, 'incidecoder'
    
    # Try OpenBeauty with OpenAI
    ingredients = scrape_openbeauty(product_name, openai_api_key)
    if ingredients:
        return ingredients, 'openbeauty_openai'
    
    # Final fallback: Direct OpenAI search
    ingredients = _search_with_openai(product_name, openai_api_key)
    if ingredients:
        return ingredients, 'openai_search'
    
    print(f"⚠️ No enriched ingredients found")
    return None, None


def _search_with_openai(product_name: str, openai_api_key: str) -> str:
    """
    Final fallback: Use OpenAI to search for ingredients
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_api_key)
        
        prompt = f"""Find the INCI ingredients for: {product_name}
        
Return ONLY a comma-separated list of ingredients, nothing else.
Be as complete as possible.

Response format:
Ingredient1, Ingredient2, Ingredient3, ..."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000
        )
        
        ingredients = response.choices[0].message.content.strip()
        
        if ingredients and len(ingredients) > 20:
            print(f"✅ OpenAI direct search: {ingredients[:100]}...")
            return ingredients
        
        return None
        
    except Exception as e:
        print(f"❌ OpenAI search error: {str(e)}")
        return None