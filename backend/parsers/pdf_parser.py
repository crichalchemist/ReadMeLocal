"""
PDF Document Parser for ReadMe
Supports PDF parsing with text extraction and position-aware filtering
"""
import re
from typing import List, Optional

import fitz  # PyMuPDF

from backend.content_filter import ContentFilter
from backend.parsers.pdf_blocks import PDFBlockExtractor


class PDFParser:
    """
    PDF document parser using PyMuPDF (fitz).
    Supports position-aware filtering to skip headers, footers, and repeated text.
    """

    def __init__(self, use_position_filtering: bool = True):
        self.content_filter = ContentFilter()
        self.use_position_filtering = use_position_filtering
        self.block_extractor = PDFBlockExtractor()

    def parse_file(self, file_path: str) -> dict:
        """Parse a PDF file and return structured content."""
        try:
            # Extract text using appropriate method
            if self.use_position_filtering:
                text_content = self._extract_with_position_filtering(file_path)
            else:
                text_content = self._extract_simple(file_path)

            # Get page count for metadata
            doc = fitz.open(file_path)
            total_pages = len(doc)
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
                "total_pages": total_pages,
            }

        except Exception as e:
            raise Exception(f"Failed to parse PDF: {str(e)}")

    def _extract_simple(self, file_path: str) -> str:
        """Extract text without position filtering (original method)."""
        doc = fitz.open(file_path)
        text_content = ""

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            text_content += page_text + "\n"

        doc.close()
        return text_content

    def _extract_with_position_filtering(self, file_path: str) -> str:
        """
        Extract text with position-aware filtering.
        Filters out header/footer zones and repeated text.
        """
        blocks = self.block_extractor.extract_blocks(file_path)

        # Find repeated headers/footers
        repeated_text = self.block_extractor.find_repeated_headers(blocks)

        # Filter blocks
        filtered_blocks = []
        for block in blocks:
            zone = self.block_extractor.classify_zone(block)

            # Skip header and footer zones
            if zone in ("header", "footer"):
                continue

            # Skip repeated text (likely running headers)
            normalized = re.sub(r"\s+", " ", block.text.strip().lower())
            if normalized in repeated_text:
                continue

            filtered_blocks.append(block)

        # Combine filtered blocks into text
        text_parts = [block.text for block in filtered_blocks]
        return "\n".join(text_parts)

    def _extract_title(self, file_path: str, text_content: str) -> str:
        """Extract title from PDF metadata or first meaningful line."""
        import os

        base_name = os.path.splitext(os.path.basename(file_path))[0]

        # Look for title in first few lines
        lines = text_content.split("\n")[:10]
        for line in lines:
            line = line.strip()
            if 10 < len(line) < 100:  # Reasonable title length
                # Skip common headers
                skip_words = ["chapter", "page", "table of contents"]
                if not any(skip in line.lower() for skip in skip_words):
                    return line

        return base_name

    def _extract_author(self, text_content: str) -> Optional[str]:
        """Try to extract author from content (basic implementation)."""
        return None

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sentences if s.strip()]
