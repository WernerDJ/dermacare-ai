"""
Agent 4: Answerer
Takes user questions and provides intelligent answers using filtered products
Uses gpt-4o-mini by default, switches to gpt-4-turbo for web search
"""

import logging
import os
from typing import List, Dict, Tuple
from agents import trace
from openai import OpenAI
from api.agents import Agent3Filter

logger = logging.getLogger(__name__)


class Agent4Answerer:
    """
    Answers user questions about skincare using product context
    
    Process:
    1. User asks a question
    2. Agent 3 filters relevant products
    3. Agent 4 uses OpenAI to answer with product context
    4. If web search needed, uses gpt-4-turbo (otherwise gpt-4o-mini)
    """
    
    def __init__(self, chroma_db_path: str = "./chroma_db", openai_api_key: str = None):
        """Initialize Agent 4"""
        self.filter_agent = Agent3Filter(chroma_db_path=chroma_db_path)
        
        if not openai_api_key:
            openai_api_key = os.getenv("OPENAI_API_KEY")
        
        self.client = OpenAI(api_key=openai_api_key)
        self.logger = logger
        self.model_default = "gpt-4o-mini"  # Fast & cheap
        self.model_search = "gpt-4-turbo"   # For web search
    
    def answer_question(self, question: str, brand_names: List[str], top_k: int = 5, use_web_search: bool = False) -> Tuple[str, List[Dict]]:
        """
        Answer a user question about skincare
        
        Args:
            question: User's question
            brand_names: Brands to search in
            top_k: Number of products to consider
            use_web_search: Whether to enable web search
            
        Returns:
            (answer, products_used)
        """
        
        with trace(f"Agent4: Answer - '{question}'"):
            # Step 1: Filter relevant products using Agent 3
            self.logger.info(f"Filtering products for: {question}")
            filtered_products = self.filter_agent.search_products(
                query=question,
                brand_names=brand_names,
                top_k=top_k
            )
            
            # Step 2: Format products for context
            products_context = self.filter_agent.format_for_agent4(filtered_products)
            
            # Step 3: Prepare system prompt - helpful and knowledgeable
            system_prompt = """You are a knowledgeable skincare expert assistant for DermaCare.

    Your role:
    - Provide expert skincare advice and recommendations
    - Answer questions about skin conditions, ingredients, routines, and products
    - Use the product database when relevant to suggest matching products
    - Provide general skincare information and best practices

    Guidelines:
    - Be helpful, friendly, and informative
    - When products are relevant, recommend them with explanations
    - If you don't have complete information, say so honestly
    - Suggest consulting a dermatologist for serious skin conditions
    - You cannot write code, hack systems, or perform non-skincare tasks

    Be conversational and genuinely helpful."""
            
            # Step 4: Create user message with product context
            user_message = f"""Answer this skincare question:

    QUESTION: {question}

    Available products from our database:
    {products_context}

    Provide helpful skincare advice. Reference products when they're relevant to the question, but feel free to give general skincare guidance as well."""
            
            # Step 5: Choose model based on web search need
            model = self.model_search if use_web_search else self.model_default
            
            # Step 6: Build tools if web search enabled
            tools = []
            if use_web_search:
                tools = [{"type": "web_search"}]
            
            # Step 7: Call OpenAI
            self.logger.info(f"Calling {model} with {len(filtered_products)} products")
            
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,
                    max_tokens=1500,
                    tools=tools if tools else None
                )
                
                answer = response.choices[0].message.content
                
                self.logger.info(f"Answer generated ({len(answer)} chars)")
                
                return answer, filtered_products
                
            except Exception as e:
                self.logger.error(f"OpenAI error: {str(e)}")
                error_answer = f"I encountered an error while answering your question: {str(e)}"
                return error_answer, []

    def get_available_brands(self) -> List[str]:
        """Get list of available brands"""
        return self.filter_agent.get_available_brands()