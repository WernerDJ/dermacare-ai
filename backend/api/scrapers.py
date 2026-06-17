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


def search_open_beauty_facts(product_name):
    """
    Search Open Beauty Facts API for product ingredients
    Returns: ingredients_string or None
    """
    try:
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


def gemini_ingredient_lookup(product_name):
    """
    Use Gemini as last resort to find ingredients.
    Strictly prompted to avoid hallucination:
    - Only return ingredients if highly confident
    - Return UNKNOWN if not sure
    - Never invent or guess ingredients
    Returns: ingredients_string or None
    """
    try:
        import google.generativeai as genai
        from django.conf import settings

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')

        words = product_name.strip().split()
        brand = words[0] if words else ''
        product = ' '.join(words[1:]) if len(words) > 1 else product_name

        prompt = f"""You are a cosmetic ingredient database. I need the INCI ingredient list for:
Brand: {brand}
Product: {product}

STRICT RULES:
1. Only return ingredients if you are CERTAIN they are correct for this EXACT product
2. If you are not 100% sure, respond with exactly: UNKNOWN
3. NEVER guess, invent, or approximate ingredients
4. NEVER use ingredients from a similar product
5. Only use ingredients you have seen on official product packaging or reliable databases
6. If the product has changed formulation over time and you are unsure which version, respond: UNKNOWN
7. Return ONLY a comma-separated INCI ingredient list, nothing else
8. No explanations, no preamble, no markdown

Respond with either the exact INCI list or the single word UNKNOWN."""

        response = model.generate_content(prompt)
        result = response.text.strip()

        if result.upper() == 'UNKNOWN' or not result:
            print(f"⚠️ Gemini: no confident ingredients for {product_name}")
            return None

        if result.count(',') < 3:
            print(f"⚠️ Gemini response does not look like an ingredient list: {result[:100]}")
            return None

        suspicious = ['i am not', "i don't", 'i cannot', 'sorry', 'unable',
                      "don't have", 'not sure', 'may contain', 'typically contains',
                      'usually contains', 'might contain', 'could contain']
        if any(phrase in result.lower() for phrase in suspicious):
            print(f"⚠️ Gemini expressed uncertainty, rejecting response")
            return None

        print(f"✅ Gemini found ingredients: {result[:100]}...")
        return result

    except Exception as e:
        print(f"❌ Gemini ingredient lookup error: {str(e)}")
        return None


def get_enriched_ingredients(product_name):
    """
    Main function: Try INCIDecoder, then Open Beauty Facts, then Gemini
    Returns: (ingredients_string, source) or (None, None)
    """
    print(f"\n🔍 Enriching ingredients for: {product_name}")

    # 1. Try INCIDecoder (with improved slug matching)
    ingredients = scrape_incidecoder(product_name)
    if ingredients:
        return ingredients, 'upc_inci'

    # 2. Try Open Beauty Facts API
    ingredients = search_open_beauty_facts(product_name)
    if ingredients:
        return ingredients, 'upc_inci'

    # 3. Gemini as last resort (strictly prompted to avoid hallucination)
    ingredients = gemini_ingredient_lookup(product_name)
    if ingredients:
        return ingredients, 'gemini'

    print(f"⚠️ No enriched ingredients found for: {product_name}")
    return None, None