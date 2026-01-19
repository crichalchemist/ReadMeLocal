"""Tests for position-aware PDF block extraction."""
import pytest
from backend.parsers.pdf_blocks import PDFBlockExtractor, TextBlock


def test_block_extractor_returns_blocks_with_coordinates():
    """Blocks should have position and font metadata."""
    # This will fail until we create the module
    extractor = PDFBlockExtractor()
    assert hasattr(extractor, 'extract_blocks')


def test_classify_header_zone():
    """Text in top 10% should be classified as header."""
    extractor = PDFBlockExtractor(header_zone_percent=0.10)
    block = TextBlock(
        text="Chapter Title",
        x0=100, y0=50, x1=400, y1=70,  # Near top
        page_height=800,
        font_size=14
    )
    assert extractor.classify_zone(block) == "header"


def test_classify_footer_zone():
    """Text in bottom 10% should be classified as footer."""
    extractor = PDFBlockExtractor(footer_zone_percent=0.10)
    block = TextBlock(
        text="Page 42",
        x0=350, y0=750, x1=400, y1=770,  # Near bottom
        page_height=800,
        font_size=10
    )
    assert extractor.classify_zone(block) == "footer"


def test_classify_body_zone():
    """Text in middle should be classified as body."""
    extractor = PDFBlockExtractor()
    block = TextBlock(
        text="Regular paragraph text here.",
        x0=100, y0=400, x1=500, y1=420,  # Middle
        page_height=800,
        font_size=12
    )
    assert extractor.classify_zone(block) == "body"


def test_detect_repeated_headers():
    """Text appearing at same Y position across multiple pages = header."""
    extractor = PDFBlockExtractor()
    blocks = [
        TextBlock(text="Book Title", x0=100, y0=50, x1=300, y1=70, page_height=800, font_size=12, page_num=0),
        TextBlock(text="Book Title", x0=100, y0=50, x1=300, y1=70, page_height=800, font_size=12, page_num=1),
        TextBlock(text="Book Title", x0=100, y0=50, x1=300, y1=70, page_height=800, font_size=12, page_num=2),
        TextBlock(text="Unique content", x0=100, y0=200, x1=500, y1=220, page_height=800, font_size=12, page_num=0),
    ]
    repeated = extractor.find_repeated_headers(blocks, threshold=3)
    assert "book title" in repeated  # Normalized lowercase
    assert "unique content" not in repeated
