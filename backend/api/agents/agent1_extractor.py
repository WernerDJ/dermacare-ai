"""
Agent 1: Enhanced Product Extractor
Extracts product metadata from PDF/DOCX/TXT documents
Returns: JSON + Error Report
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
    """
    Extracts product information from documents.

    Metadata fields extracted:
    - Brand (provided by admin)
    - Product (name)
    - Skin_type
    - Treatment_kind
    - Skin_problems (array)
    - Body_parts (array)
    - Ingredients
    - Usage
    - Benefits
    """

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        self.logger = logger

    def extract_from_document(
        self,
        file_path: str,
        brand_name: str,
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract all products from a document.

        NOTE:
        This method intentionally DOES NOT create a trace.
        The caller (view, task, test, etc.) is responsible for
        creating the workflow trace.
        """

        self.logger.info(
            "Starting extraction: %s | Brand: %s",
            file_path,
            brand_name,
        )

        try:
            raw_text = self._parse_document(file_path)
            self.logger.info(
                "Document parsed successfully (%d characters)",
                len(raw_text),
            )

        except Exception as e:
            self.logger.exception("Document parsing failed")

            return [], [
                {
                    "product": "ENTIRE_DOCUMENT",
                    "reason": f"Parse error: {e}",
                }
            ]

        products, errors = self._extract_products_from_text(
            raw_text,
            brand_name,
        )

        self.logger.info(
            "Extraction finished. Products=%d Errors=%d",
            len(products),
            len(errors),
        )

        return products, errors

    def _parse_document(self, file_path: str) -> str:
        """Parse PDF, DOCX or TXT into raw text."""

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

            for page_number, page in enumerate(reader.pages):

                try:
                    text.append(page.extract_text())

                except Exception as e:
                    self.logger.warning(
                        "Failed to extract page %d: %s",
                        page_number,
                        e,
                    )

        return "\n".join(text)

    def _parse_docx(self, file_path: str) -> str:
        """Extract text from DOCX."""

        doc = Document(file_path)

        return "\n".join(
            paragraph.text
            for paragraph in doc.paragraphs
        )

    def _parse_txt(self, file_path: str) -> str:
        """Extract text from TXT."""

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _extract_products_from_text(
        self,
        text: str,
        brand_name: str,
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Use OpenAI to extract structured product data.

        NOTE:
        No trace is created here.
        """

        self.logger.info("Calling OpenAI model %s", self.model)

        prompt = f"""You are a cosmetics database expert. Extract ALL products from this document.

BRAND NAME: {brand_name}

For EACH product found, extract these fields:

1. Product (name)
2. Skin_type
3. Treatment_kind
4. Skin_problems (array)
5. Body_parts (array)
6. Ingredients
7. Usage
8. Benefits

RULES:

- Extract EVERY product mentioned.
- If a field is missing, use "Unknown".
- Keep ingredient lists complete.
- Return ONLY a valid JSON array.

[
  {{
    "product": "Product Name",
    "skin_type": "All",
    "treatment_kind": "Cleansing",
    "skin_problems": ["Dehydration"],
    "body_parts": ["Face"],
    "ingredients": "Water, Glycerin",
    "usage": "Morning and evening",
    "benefits": "Hydration"
  }}
]

TEXT:

{text[:10000]}
"""

        try:

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.3,
                max_tokens=4000,
            )

            response_text = response.choices[0].message.content.strip()

            if "```json" in response_text:
                response_text = (
                    response_text
                    .split("```json")[1]
                    .split("```")[0]
                    .strip()
                )

            elif "```" in response_text:
                response_text = (
                    response_text
                    .split("```")[1]
                    .split("```")[0]
                    .strip()
                )

            products_raw = json.loads(response_text)

            products = []
            errors = []

            for index, product in enumerate(products_raw):

                try:
                    cleaned = self._validate_product(
                        product,
                        brand_name,
                    )

                    products.append(cleaned)

                except ValueError as e:

                    errors.append(
                        {
                            "product": product.get(
                                "product",
                                f"Product {index}",
                            ),
                            "reason": str(e),
                        }
                    )

            self.logger.info(
                "OpenAI returned %d valid products",
                len(products),
            )

            return products, errors

        except json.JSONDecodeError as e:

            self.logger.exception("JSON decoding failed")

            return [], [
                {
                    "product": "EXTRACTION",
                    "reason": f"JSON error: {e}",
                }
            ]

        except Exception as e:

            self.logger.exception("OpenAI request failed")

            return [], [
                {
                    "product": "EXTRACTION",
                    "reason": f"API error: {e}",
                }
            ]

    def _validate_product(
        self,
        product: Dict,
        brand_name: str,
    ) -> Dict:

        if (
            not product.get("product")
            or product.get("product") == "Unknown"
        ):
            raise ValueError("Product name is required")

        return {
            "brand": brand_name,
            "product": product.get("product", "").strip(),
            "skin_type": product.get("skin_type", "Unknown"),
            "treatment_kind": product.get(
                "treatment_kind",
                "Unknown",
            ),
            "skin_problems": self._parse_array(
                product.get("skin_problems", [])
            ),
            "body_parts": self._parse_array(
                product.get("body_parts", [])
            ),
            "ingredients": product.get(
                "ingredients",
                "Unknown",
            ),
            "usage": product.get(
                "usage",
                "Unknown",
            ),
            "benefits": product.get(
                "benefits",
                "Unknown",
            ),
        }

    def _parse_array(self, value) -> List[str]:

        if isinstance(value, list):
            return [
                str(v).strip()
                for v in value
                if v
            ]

        if isinstance(value, str):
            separator = "|" if "|" in value else ","

            return [
                v.strip()
                for v in value.split(separator)
                if v.strip()
            ]

        return []

    def generate_error_report(
        self,
        errors: List[Dict],
    ) -> str:

        if not errors:
            return "✅ No errors - all products extracted successfully!"

        report = (
            f"⚠️ EXTRACTION REPORT: {len(errors)} products failed\n"
        )

        report += "=" * 60 + "\n\n"

        for error in errors:
            report += (
                f"❌ {error.get('product', 'Unknown')}\n"
                f"   Reason: {error.get('reason', 'Unknown error')}\n\n"
            )

        report += "\n" + "=" * 60 + "\n"
        report += (
            "💡 Create a TXT with failed products:\n"
        )
        report += (
            "Brand | Product | Skin Type | Treatment | "
            "Skin Problems | Body Parts | Ingredients | "
            "Usage | Benefits\n"
        )

        return report