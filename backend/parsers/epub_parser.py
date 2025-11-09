"""
EPUB Document Parser for ReadMe
Supports EPUB parsing with chapter extraction and text processing
"""
from typing import List, Optional
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from backend.content_filter import ContentFilter


class EPUBParser:
    """
    EPUB document parser using ebooklib
    """

    def __init__(self):
        self.content_filter = ContentFilter()

    def parse_file(self, file_path: str) -> dict:
        """
        Parse an EPUB file and return structured content
        """
        try:
            book = epub.read_epub(file_path)
            text_content = ""

            # Extract text from all chapters
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.extract()
                    # Get text
                    chapter_text = soup.get_text()
                    text_content += chapter_text + "\n\n"

            # Apply content filtering
            filtered_text = self.content_filter.filter_text(text_content)

            # Split into sentences
            sentences = self._split_sentences(filtered_text)

            return {
                "title": self._extract_title(book),
                "author": self._extract_author(book),
                "content": sentences,
                "num_sentences": len(sentences),
                "total_chapters": len([item for item in book.get_items() if item.get_type() == ebooklib.ITEM_DOCUMENT])
            }

        except Exception as e:
            raise Exception(f"Failed to parse EPUB: {str(e)}")

    def _extract_title(self, book) -> str:
        """Extract title from EPUB metadata"""
        title = book.get_metadata('DC', 'title')
        if title:
            return str(title[0][0])
        return "Untitled EPUB"

    def _extract_author(self, book) -> Optional[str]:
        """Extract author from EPUB metadata"""
        author = book.get_metadata('DC', 'creator')
        if author:
            return str(author[0][0])
        return None

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        # Simple sentence splitting - could be enhanced
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]