from django.test import TestCase
import os
from dotenv import load_dotenv
from api.agents import Agent4Answerer

load_dotenv()


class Agent4AnswererTest(TestCase):
    """Test Agent 4: Question Answering"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.answerer = Agent4Answerer(
            chroma_db_path="/app/chroma_db",
            openai_api_key=self.openai_api_key
        )
    
    def test_answer_moisturizing_question(self):
        """Test answering a moisturizing question"""
        brands = self.answerer.get_available_brands()
        self.assertGreater(len(brands), 0)
        
        answer, products = self.answerer.answer_question(
            question="What's the best moisturizer for dry skin?",
            brand_names=brands
        )
        
        self.assertIsNotNone(answer)
        self.assertGreater(len(answer), 50)
        self.assertGreater(len(products), 0)
        print(f"\n✅ Answer generated:\n{answer[:300]}...")
    
    def test_answer_cleansing_question(self):
        """Test answering a cleansing question"""
        brands = self.answerer.get_available_brands()
        
        answer, products = self.answerer.answer_question(
            question="What cleansing products do you recommend for sensitive skin?",
            brand_names=brands
        )
        
        self.assertIsNotNone(answer)
        self.assertGreater(len(answer), 50)
        print(f"\n✅ Answer: {answer[:300]}...")
    
    def test_jailbreak_resistance(self):
        """Test that Agent 4 resists jailbreak attempts"""
        result = self.answerer.validate_jailbreak_resistance()
        self.assertTrue(result, "Agent 4 should resist jailbreak attempts")
        print("\n✅ Jailbreak resistance: PASSED")
    
    def test_no_product_found_graceful(self):
        """Test graceful handling when no products found"""
        answer, products = self.answerer.answer_question(
            question="xyzabc nonexistent product xyz",
            brand_names=self.answerer.get_available_brands()
        )
        
        self.assertIsNotNone(answer)
        print(f"\n✅ Graceful handling: {answer[:200]}...")