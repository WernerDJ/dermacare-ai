"""
Test script for Agent 1 + Agent 2
Extract products → Vectorize → Store in Chroma → Search
"""

import os
import sys
import json
import django

# Parent directory to path so we can import dermacare
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dermacare.settings')
django.setup()

from api.agents import Agent1Extractor, Agent2Vectorizer
from dotenv import load_dotenv
import glob

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("❌ OPENAI_API_KEY not found in .env")
    sys.exit(1)

print("✅ API Key loaded")

# ============================================================
# AGENT 1: Extract Products
# ============================================================
print("\n" + "="*60)
print("🔍 AGENT 1: EXTRACT PRODUCTS")
print("="*60)

extractor = Agent1Extractor(api_key=openai_api_key)
print("✅ Agent 1 initialized")

pdfs = glob.glob("/app/uploads/*.pdf")
if not pdfs:
    print("❌ No PDFs found")
    sys.exit(1)

pdf_path = pdfs[0]
print(f"📄 Using: {os.path.basename(pdf_path)}")

products, errors = extractor.extract_from_document(
    file_path=pdf_path,
    brand_name="Biotherm"
)

print(f"\n✅ Extracted {len(products)} products, {len(errors)} errors")

if products:
    print(f"\n📦 Sample Product:")
    print(json.dumps(products[0], indent=2))

# ============================================================
# AGENT 2: Vectorize Products
# ============================================================
print("\n" + "="*60)
print("🧠 AGENT 2: VECTORIZE & STORE")
print("="*60)

vectorizer = Agent2Vectorizer(chroma_db_path="/app/chroma_db")
print("✅ Agent 2 initialized")

stored_count, enrichment_log = vectorizer.vectorize_products(
    products=products,
    brand_name="Biotherm"
)

print(f"\n✅ Stored {stored_count} products in Chroma")

print(f"\n📊 Enrichment Report:")
for log in enrichment_log[:5]:
    if log['enriched']:
        print(f"   ✅ {log['product']}: Enriched from {log['source']}")
    else:
        print(f"   ⚠️ {log['product']}: {log['reason']}")

if len(enrichment_log) > 5:
    print(f"   ... and {len(enrichment_log) - 5} more")

# ============================================================
# AGENT 2: Search Products
# ============================================================
print("\n" + "="*60)
print("🔎 AGENT 2: SEARCH PRODUCTS")
print("="*60)

test_queries = [
    "moisturizing for dry skin",
    "anti-aging treatment",
    "cleansing face"
]

for query in test_queries:
    print(f"\n🔍 Query: '{query}'")
    results = vectorizer.search_products(
        brand_name="Biotherm",
        query=query,
        n_results=3
    )
    
    if results:
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            print(f"   {i}. {metadata.get('product', 'Unknown')}")
            print(f"      Type: {metadata.get('treatment_kind', 'N/A')}")
            print(f"      Skin Type: {metadata.get('skin_type', 'N/A')}")
    else:
        print("   No results found")

# ============================================================
# Collection Stats
# ============================================================
print("\n" + "="*60)
print("📊 COLLECTION STATS")
print("="*60)

stats = vectorizer.get_collection_stats("Biotherm")
print(f"\n{json.dumps(stats, indent=2)}")

print("\n✅ Agent 1 + Agent 2 Test Complete!")