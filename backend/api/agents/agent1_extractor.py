"""
Agent 1: Product-Targeted Extractor
Takes a list of product names and extracts metadata for each
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import PyPDF2
from docx import Document
from openai import OpenAI

logger = logging.getLogger(__name__)

class Agent1Extractor:
    """Extracts metadata for specified products."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        self.logger = logger
    
    def extract_from_document(
        self,
        file_path: str,
        brand_name: str,
        product_names: List[str],
    ) -> Tuple[List[Dict], List[Dict]]:
        """Extract metadata for each product in the list."""
        self.logger.info(
            "Starting extraction: %s | Brand: %s | Products: %d",
            file_path,
            brand_name,
            len(product_names),
        )
        try:
            raw_text = self._parse_document(file_path)
            self.logger.info("Document parsed (%d chars)", len(raw_text))
        except Exception as e:
            self.logger.exception("Document parsing failed")
            return [], [{"product": "ENTIRE_DOCUMENT", "reason": str(e)}]
        
        products = []
        errors = []
        
        # Extract metadata for each product
        for product_name in product_names:
            try:
                product = self._extract_product(product_name, brand_name, raw_text)
                if product:
                    products.append(product)
                else:
                    errors.append({
                        "product": product_name,
                        "reason": "Not found in document"
                    })
            except Exception as e:
                self.logger.warning(f"Failed to extract {product_name}: {e}")
                errors.append({
                    "product": product_name,
                    "reason": str(e)
                })
        
        self.logger.info(
            "Extraction finished. Found=%d Errors=%d",
            len(products),
            len(errors),
        )
        return products, errors
    
    def _parse_document(self, file_path: str) -> str:
        """Parse PDF, DOCX or TXT."""
        extension = Path(file_path).suffix.lower()
        if extension == ".pdf":
            return self._parse_pdf(file_path)
        if extension == ".docx":
            return self._parse_docx(file_path)
        if extension == ".txt":
            return self._parse_txt(file_path)
        raise ValueError(f"Unsupported file type: {extension}")
    
    def _parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF."""
        text = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                try:
                    text.append(page.extract_text())
                except Exception as e:
                    self.logger.warning(f"Failed to extract page: {e}")
        return "\n".join(text)
    
    def _parse_docx(self, file_path: str) -> str:
        """Extract text from DOCX."""
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    
    def _parse_txt(self, file_path: str) -> str:
        """Extract text from TXT."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _ensure_string(self, value) -> str:
        """Ensure value is a string."""
        if isinstance(value, list):
            return ', '.join(str(v) for v in value)
        return str(value)
    
    def _extract_product(self, product_name: str, brand_name: str, document_text: str) -> Dict:
        """Extract metadata for a specific product."""
        
        # Find product in document
        product_context = self._find_product_section(product_name, document_text)
        
        if not product_context:
            return None
        
        # Use AI to extract metadata
        prompt = f"""Extract metadata for this {brand_name} product:

Product Name: {product_name}

Product Description from document:
{product_context[:2000]}

Extract and return JSON only:
{{
  "product": "{product_name}",
  "skin_type": "All|Dry|Oily|Sensitive|Combination|Unknown",
  "treatment_kind": "Cleanser|Moisturizer|Toner|Serum|Mask|etc",
  "skin_problems": ["problem1", "problem2"],
  "body_parts": ["Face", "Body", "etc"],
  "life_stage": "Babies|Children|Teenagers|Adults|Menopausal|Post-Menopausal|All Ages|Unknown",
  "gender": "Men|Women|Unisex|Unknown",
  "ingredients": "List of ingredients",
  "usage": "How to use",
  "benefits": "What it does"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1000,
            )
            
            text = response.choices[0].message.content.strip()
            
            # Clean markdown
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            
            return {
                "brand": brand_name,
                "product": product_name,
                "skin_type": str(data.get("skin_type", "Unknown")),
                "treatment_kind": str(data.get("treatment_kind", "Unknown")),
                "skin_problems": self._parse_array(data.get("skin_problems", [])),
                "body_parts": self._parse_array(data.get("body_parts", [])),
                "life_stage": str(data.get("life_stage", "Unknown")),
                "gender": str(data.get("gender", "Unknown")),
                "ingredients": self._ensure_string(data.get("ingredients", "Unknown")),
                "usage": str(data.get("usage", "Unknown")),
                "benefits": str(data.get("benefits", "Unknown")),
            }

        except Exception as e:
            self.logger.error(f"Metadata extraction failed for {product_name}: {e}")
            return None
    
    def _find_product_section(self, product_name: str, document_text: str) -> str:
        """Find the section of text about this product."""
        
        # Search for product name (case-insensitive)
        lines = document_text.split('\n')
        result = []
        found = False
        
        for i, line in enumerate(lines):
            if product_name.lower() in line.lower():
                found = True
                # Get context around the product
                start = max(0, i - 2)
                end = min(len(lines), i + 20)
                result = lines[start:end]
                break
        
        if result:
            return '\n'.join(result)
        
        return None
    
    def _parse_array(self, value) -> List[str]:
        """Parse array from various formats."""
        if isinstance(value, list):
            return [str(v).strip() for v in value if v]
        if isinstance(value, str):
            sep = "|" if "|" in value else ","
            return [v.strip() for v in value.split(sep) if v.strip()]
        return []
    
    def generate_error_report(self, errors: List[Dict]) -> str:
        """Generate error report."""
        if not errors:
            return "✅ All products extracted successfully!"
        report = f"⚠️ Failed to extract {len(errors)} products:\n\n"
        for error in errors:
            report += f"❌ {error['product']}\n   Reason: {error['reason']}\n"
        return report