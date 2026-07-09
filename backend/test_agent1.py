import os
import sys
import json
import django
from agents import trace


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dermacare.settings')
django.setup()

from api.agents import Agent1Extractor
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("❌ OPENAI_API_KEY not found in .env")
    sys.exit(1)

print("✅ API Key loaded")

extractor = Agent1Extractor(api_key=openai_api_key)
print("✅ Agent 1 initialized")

import glob
pdfs = glob.glob("/app/uploads/*.pdf")
if not pdfs:
    print("❌ No PDFs found in /app/uploads/")
    sys.exit(1)

pdf_path = pdfs[0]
print(f"📄 Testing with: {os.path.basename(pdf_path)}")

print("\n🔍 Extracting products...")
with trace("Agent 1 - Full Extraction Test"):
    products, errors = extractor.extract_from_document(
        file_path=pdf_path,
        brand_name="Biotherm"
    )

print(f"\n✅ Extraction Complete!")
print(f"   Products: {len(products)}")
print(f"   Errors: {len(errors)}")

if products:
    print(f"\n📦 First Product:")
    print(json.dumps(products[0], indent=2))

if errors:
    report = extractor.generate_error_report(errors)
    print(f"\n⚠️ Errors:\n{report}")
