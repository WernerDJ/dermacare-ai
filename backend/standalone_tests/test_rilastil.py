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

print("="*60)
print("🧪 Testing with DOCX: Rilastil")
print("="*60)

# Agent 1
extractor = Agent1Extractor(api_key=openai_api_key)

docx_files = glob.glob("/app/uploads/*.docx")
if not docx_files:
    print("❌ No DOCX files found")
    sys.exit(1)

docx_path = docx_files[0]
print(f"📄 Testing: {os.path.basename(docx_path)}")

products, errors = extractor.extract_from_document(
    file_path=docx_path,
    brand_name="Rilastil"
)

print(f"\n✅ Extracted: {len(products)} products")

# Agent 2
vectorizer = Agent2Vectorizer(chroma_db_path="/app/chroma_db")

stored_count, enrichment_log = vectorizer.vectorize_products(
    products=products,
    brand_name="Rilastil"
)

print(f"✅ Stored: {stored_count} products")

enriched_count = sum(1 for log in enrichment_log if log.get('enriched'))
print(f"✅ Enriched: {enriched_count}/{len(products)} products")

# Search test
print("\n🔍 Search Test:")
results = vectorizer.search_products("Rilastil", "moisturizing anti-aging", n_results=3)
for i, r in enumerate(results, 1):
    print(f"   {i}. {r['metadata'].get('product')}")

print("\n✅ Rilastil Test Complete!")
