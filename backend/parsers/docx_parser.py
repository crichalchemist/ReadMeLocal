"""
DOCX Document Parser for ReadMe
Supports Microsoft Word document parsing with text extraction
"""
from typing import List, Optional
import docx2txt
from backend.content_filter import ContentFilter


class DOCXParser:
    """
    DOCX document parser using docx2txt
    """

    def __init__(self):
        self.content_filter = ContentFilter()

    def parse_file(self, file_path: str) -> dict:
        """
        Parse a DOCX file and return structured content
        """
        try:
            # Extract text from DOCX
            text_content = docx2txt.process(file_path)

            if not text_content:
                raise Exception("No text content found in DOCX file")

            # Apply content filtering
            filtered_text = self.content_filter.filter_text(text_content)

            # Split into sentences
            sentences = self._split_sentences(filtered_text)

            return {
                "title": self._extract_title(file_path, text_content),
                "author": None,  # docx2txt doesn't extract metadata easily
                "content": sentences,
                "num_sentences": len(sentences),
                "source": "docx"
            }

        except Exception as e:
            raise Exception(f"Failed to parse DOCX: {str(e)}")

    def _extract_title(self, file_path: str, text_content: str) -> str:
        """Extract title from file path or first meaningful line"""
        import os
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        # Look for title in first few lines
        lines = text_content.split('\n')[:5]  # Check first 5 lines
        for line in lines:
            line = line.strip()
            if len(line) > 10 and len(line) < 100:  # Reasonable title length
                # Skip common headers
                if not any(skip in line.lower() for skip in ['chapter', 'page', 'table of contents']):
                    return line

        return base_name

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        # Simple sentence splitting - could be enhanced
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]