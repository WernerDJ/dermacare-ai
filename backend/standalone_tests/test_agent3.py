import os
import sys
import django

# Parent directory to path so we can import dermacare
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dermacare.settings')
django.setup()

from api.agents import Agent3Filter

print("="*60)
print("🔎 Testing Agent 3: Filter")
print("="*60)

filter_agent = Agent3Filter(chroma_db_path="/app/chroma_db")

# Get available brands
brands = filter_agent.get_available_brands()
print(f"\n✅ Available brands: {brands}")

# Test queries
test_queries = [
    "moisturizing cream for dry skin",
    "anti-aging treatment",
    "cleansing product for sensitive skin"
]

for query in test_queries:
    print(f"\n🔍 Query: '{query}'")
    
    results = filter_agent.filter_products(
        query=query,
        brand_names=brands,
        top_k=3
    )
    
    print(f"   Found {len(results)} results:")
    for r in results:
        print(f"   - {r['metadata'].get('product')} ({r['brand']})")
    
    # Format for Agent 4
    formatted = filter_agent.format_for_agent4(results)
    print(f"\nFormatted for Agent 4:\n{formatted}")

print("✅ Agent 3 Test Complete!")
