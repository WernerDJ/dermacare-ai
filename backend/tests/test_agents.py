from django.test import TestCase
import os
import shutil
import json
import glob
from dotenv import load_dotenv
from api.agents import Agent1Extractor, Agent2Vectorizer, Agent3Filter

load_dotenv()


class Agent1And2IntegrationTest(TestCase):
    """Test Agent 1 + 2: Extract and Vectorize BOTH brands"""
    
    @classmethod
    def setUpClass(cls):
        chroma_path = "/app/chroma_db"
        super().setUpClass()
    
    def setUp(self):
        """Set up test fixtures"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.extractor = Agent1Extractor(api_key=self.openai_api_key)
        self.vectorizer = Agent2Vectorizer(chroma_db_path="/app/chroma_db")
    
    def test_01_extract_and_vectorize_biotherm_pdf(self):
        """
        FIRST: Extract Biotherm PDF and vectorize into Chroma
        This must run first so Biotherm is available for Agent3 tests
        """
        pdfs = glob.glob("/app/tests/uploads/*iotherm*.pdf")
        self.assertGreater(len(pdfs), 0, "No Biotherm PDF found")
        
        # Step 1: Extract
        products, errors = self.extractor.extract_from_document(
            file_path=pdfs[0],
            brand_name="Biotherm"
        )
        
        self.assertGreater(len(products), 0, "Biotherm extraction failed")
        print(f"\n✅ Extracted {len(products)} Biotherm products")
        
        # Step 2: Vectorize and store in Chroma
        stored_count, enrichment_log = self.vectorizer.vectorize_products(
            products=products,
            brand_name="Biotherm"
        )
        
        self.assertEqual(stored_count, len(products))
        print(f"✅ Vectorized and stored {stored_count} Biotherm products")
    
    def test_02_extract_and_vectorize_rilastil_docx(self):
        """
        SECOND: Extract Rilastil DOCX and vectorize into Chroma
        Now both Biotherm and Rilastil are in the database
        """
        docx_files = glob.glob("/app/tests/uploads/*ilastil*.docx")
        self.assertGreater(len(docx_files), 0, "No Rilastil DOCX found")
        
        # Step 1: Extract
        products, errors = self.extractor.extract_from_document(
            file_path=docx_files[0],
            brand_name="Rilastil"
        )
        
        self.assertGreater(len(products), 0, "Rilastil extraction failed")
        print(f"\n✅ Extracted {len(products)} Rilastil products")
        
        # Step 2: Vectorize and store in Chroma
        stored_count, enrichment_log = self.vectorizer.vectorize_products(
            products=products,
            brand_name="Rilastil"
        )
        
        self.assertEqual(stored_count, len(products))
        print(f"✅ Vectorized and stored {stored_count} Rilastil products")


class Agent3FilterTest(TestCase):
    """Test Agent 3: Search (NOW both brands are in Chroma!)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.filter_agent = Agent3Filter(chroma_db_path="/app/chroma_db")
    
    def test_03_available_brands(self):
        """Verify both brands are in Chroma"""
        brands = self.filter_agent.get_available_brands()
        
        print(f"\n✅ Available brands: {brands}")
        self.assertGreater(len(brands), 0, "No brands in Chroma")
        self.assertIn("Biotherm", [b for b in brands if "biotherm" in b.lower()])
        self.assertIn("Rilastil", [b for b in brands if "rilastil" in b.lower()])
    
    def test_04_search_moisturizing(self):
        """Search for moisturizing products across both brands"""
        brands = self.filter_agent.get_available_brands()
        self.assertGreater(len(brands), 0, "No brands found")
        
        results = self.filter_agent.search_products(
            query="moisturizing cream for dry skin",
            brand_names=brands,
            top_k=3
        )
        
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 3)
        print(f"\n✅ Found {len(results)} moisturizing products")
        
        for r in results:
            print(f"   - {r['metadata'].get('product')} ({r['brand']})")
    
    def test_05_search_cleansing(self):
        """Search for cleansing products"""
        brands = self.filter_agent.get_available_brands()
        
        results = self.filter_agent.search_products(
            query="cleansing product for sensitive skin",
            brand_names=brands,
            top_k=3
        )
        
        self.assertIsInstance(results, list)
        print(f"\n✅ Found {len(results)} cleansing products")
        
        for r in results:
            print(f"   - {r['metadata'].get('product')} ({r['brand']})")
    
    def test_06_format_for_agent4(self):
        """Test formatting search results for Agent 4"""
        brands = self.filter_agent.get_available_brands()
        
        results = self.filter_agent.search_products(
            query="anti-aging treatment",
            brand_names=brands,
            top_k=2
        )
        
        if results:
            formatted = self.filter_agent.format_for_agent4(results)
            self.assertIn("RELEVANT PRODUCTS", formatted)
            self.assertIn("Brand:", formatted)
            self.assertIn("Ingredients:", formatted)
            print(f"\n✅ Formatted for Agent 4:\n{formatted[:500]}...")


class EndToEndTest(TestCase):
    """End-to-end validation"""
    
    def test_07_full_pipeline_validation(self):
        """Validate complete pipeline works"""
        filter_agent = Agent3Filter(chroma_db_path="/app/chroma_db")
        
        brands = filter_agent.get_available_brands()
        self.assertGreaterEqual(len(brands), 2, "Should have at least 2 brands")
        
        # Search across all brands
        results = filter_agent.search_products(
            query="skincare moisturizer",
            brand_names=brands,
            top_k=5
        )
        
        self.assertGreater(len(results), 0, "Search should return results")
        
        # Format for Agent 4
        formatted = filter_agent.format_for_agent4(results)
        self.assertIn("RELEVANT PRODUCTS", formatted)
        
        print(f"\n✅ End-to-end validation passed!")
        print(f"   - Brands: {len(brands)}")
        print(f"   - Search results: {len(results)}")