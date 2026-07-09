"""
Multi-Agent System for DermaCare

Agent 1: Extractor - Extracts products from documents
Agent 2: Vectorizer - Creates vector embeddings (Chroma)
Agent 3: Filter - Filters relevant products for query
Agent 4: Answerer - Answers user questions with context
"""

from .agent1_extractor import Agent1Extractor
from .agent2_vectorizer import Agent2Vectorizer

__all__ = ['Agent1Extractor', 'Agent2Vectorizer']

