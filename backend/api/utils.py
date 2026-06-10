import google.generativeai as genai
from django.conf import settings
import json


def ask_gemini_question(question, products, ingredients, brands):
    """
    Ask Gemini a question based on loaded product portfolios
    
    Args:
        question: User's question
        products: List of product dicts
        ingredients: Dict of {product_name: ingredients_list}
        brands: List of brand names
    
    Returns:
        (answer_text, tokens_used)
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    system_instruction = f"""
    You are a skincare advisor. Answer questions based ONLY on the provided product data.
    
    CRITICAL RULES:
    1. Do NOT add information from your training data
    2. Do NOT mention products or brands not in the provided list
    3. Only discuss: {', '.join(brands)}
    4. Be helpful and specific to their question
    """
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_instruction
    )
    
    # Format context
    context = "AVAILABLE PRODUCTS:\n\n"
    
    for product in products:
        context += f"• {product['name']}\n"
        if product.get('description'):
            context += f"  Description: {product['description']}\n"
        if product.get('benefits'):
            context += f"  Benefits: {product['benefits']}\n"
        if product.get('category'):
            context += f"  Category: {product['category']}\n"
        context += "\n"
    
    # Add ingredients
    if ingredients:
        context += "\nINGREDIENTS BY PRODUCT:\n\n"
        for product_name, ingredients_str in ingredients.items():
            context += f"• {product_name}: {ingredients_str}\n"
    
    # Prepare prompt
    prompt = f"""{context}

USER QUESTION: {question}

Answer based ONLY on the products and data above."""
    
    # Get response
    response = model.generate_content(prompt)
    
    # Extract token count (approximate)
    tokens_used = len(prompt.split()) + len(response.text.split())
    
    return response.text, tokens_used


def prepare_analysis_context(portfolios):
    """
    Prepare full context from multiple portfolios
    
    Args:
        portfolios: QuerySet of BrandPortfolio objects
    
    Returns:
        Dict with products and ingredients
    """
    context = {
        'products': [],
        'ingredients': {},
        'brands': []
    }
    
    for portfolio in portfolios:
        context['brands'].append(portfolio.name)
        
        for product in portfolio.products.all():
            context['products'].append({
                'name': product.name,
                'brand': portfolio.name,
                'description': product.description,
                'category': product.category,
                'benefits': product.benefits,
                'how_to_use': product.how_to_use,
                'pdf_ingredients': product.pdf_ingredients
            })
            
            # Add API ingredients if available
            if hasattr(product, 'ingredient'):
                context['ingredients'][product.name] = {
                    'list': product.ingredient.ingredients_list,
                    'source': product.ingredient.source,
                    'barcode': product.ingredient.barcode
                }
    
    return context


def validate_portfolio_data(data):
    """
    Validate portfolio data structure
    
    Args:
        data: Portfolio data dict
    
    Returns:
        (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Data must be a dictionary"
    
    required_fields = ['product_name', 'products']
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    if not isinstance(data['products'], list):
        return False, "Products must be a list"
    
    if len(data['products']) == 0:
        return False, "Must have at least one product"
    
    for product in data['products']:
        if not isinstance(product, dict) or 'name' not in product:
            return False, "Each product must have a name"
    
    return True, None