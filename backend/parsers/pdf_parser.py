"""
PDF Document Parser for ReadMe
Supports PDF parsing with text extraction and basic structure detection
"""
from typing import List, Optional
import fitz  # PyMuPDF
from backend.content_filter import ContentFilter


class PDFParser:
    """
    PDF document parser using PyMuPDF (fitz)
    """

    def __init__(self):
        self.content_filter = ContentFilter()

    def parse_file(self, file_path: str) -> dict:
        """
        Parse a PDF file and return structured content
        """
        try:
            doc = fitz.open(file_path)
            text_content = ""

            # Extract text from all pages
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                text_content += page_text + "\n"

            doc.close()

            # Apply content filtering
            filtered_text = self.content_filter.filter_text(text_content)

            # Split into sentences
            sentences = self._split_sentences(filtered_text)

            return {
                "title": self._extract_title(file_path, text_content),
                "author": self._extract_author(text_content),
                "content": sentences,
                "num_sentences": len(sentences),
                "total_pages": len(doc)
            }

        except Exception as e:
            raise Exception(f"Failed to parse PDF: {str(e)}")

    def _extract_title(self, file_path: str, text_content: str) -> str:
        """Extract title from PDF metadata or first meaningful line"""
        # Try to get from file path first
        import os
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        # Look for title in first few lines
        lines = text_content.split('\n')[:10]  # Check first 10 lines
        for line in lines:
            line = line.strip()
            if len(line) > 10 and len(line) < 100:  # Reasonable title length
                # Skip common headers
                if not any(skip in line.lower() for skip in ['chapter', 'page', 'table of contents']):
                    return line

        return base_name

    def _extract_author(self, text_content: str) -> Optional[str]:
        """Try to extract author from content (basic implementation)"""
        # This is a simple implementation - could be enhanced with better heuristics
        return None

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        # Simple sentence splitting - could be enhanced
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]