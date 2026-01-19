"""Tests for PDF parser with position-aware filtering."""
import sys
import pytest
from unittest.mock import MagicMock, patch

# Mock fitz module before importing PDFParser
mock_fitz = MagicMock()
sys.modules['fitz'] = mock_fitz

from backend.parsers.pdf_parser import PDFParser
from backend.parsers.pdf_blocks import TextBlock


def test_parser_uses_position_filtering():
    """Parser should filter out header/footer zones."""
    parser = PDFParser()
    # Verify the parser has position-aware capability
    assert hasattr(parser, 'use_position_filtering')
    assert parser.use_position_filtering is True


def test_parser_can_disable_position_filtering():
    """Parser should allow disabling position filtering."""
    parser = PDFParser(use_position_filtering=False)
    assert parser.use_position_filtering is False


def test_parser_has_extract_methods():
    """Parser should have both extraction methods."""
    parser = PDFParser()
    assert hasattr(parser, '_extract_with_position_filtering')
    assert hasattr(parser, '_extract_simple')
    assert callable(parser._extract_with_position_filtering)
    assert callable(parser._extract_simple)


def test_position_filtering_excludes_header_and_footer_zones():
    """
    Verify that position filtering actually removes header/footer content.
    This tests the core filtering behavior with mock data.
    """
    # Create test blocks representing different zones on a 1000px tall page:
    # - Header zone: y < 100 (10% of page height)
    # - Footer zone: y > 900 (10% from bottom)
    # - Body zone: 100 <= y <= 900
    page_height = 1000.0

    test_blocks = [
        # Header zone block (y0=50, should be filtered out)
        TextBlock(
            text="Chapter 1 - Running Header",
            x0=100, y0=50, x1=500, y1=80,
            page_height=page_height,
            font_size=10,
            page_num=0,
        ),
        # Body zone block (y0=200, should be kept)
        TextBlock(
            text="This is the main body content that should be preserved.",
            x0=50, y0=200, x1=550, y1=250,
            page_height=page_height,
            font_size=12,
            page_num=0,
        ),
        # Another body block (y0=400, should be kept)
        TextBlock(
            text="More important content in the middle of the page.",
            x0=50, y0=400, x1=550, y1=450,
            page_height=page_height,
            font_size=12,
            page_num=0,
        ),
        # Footer zone block (y0=950, should be filtered out)
        TextBlock(
            text="Page 1 of 10",
            x0=250, y0=950, x1=350, y1=980,
            page_height=page_height,
            font_size=9,
            page_num=0,
        ),
    ]

    parser = PDFParser(use_position_filtering=True)

    # Mock the block extractor to return our test blocks
    with patch.object(
        parser.block_extractor,
        'extract_blocks',
        return_value=(test_blocks, 5)  # 5 pages
    ):
        text, page_count = parser._extract_with_position_filtering("/fake/path.pdf")

    # Verify page count is passed through
    assert page_count == 5

    # Verify header content was filtered out
    assert "Running Header" not in text
    assert "Chapter 1" not in text

    # Verify footer content was filtered out
    assert "Page 1 of 10" not in text

    # Verify body content was preserved
    assert "main body content" in text
    assert "More important content" in text


def test_position_filtering_excludes_repeated_text():
    """
    Verify that repeated text (like running headers) is filtered out
    even when it appears in the body zone.
    """
    page_height = 1000.0

    # Same repeated text appearing across multiple pages in body zone
    test_blocks = [
        # Repeated header text on page 0 (in body zone position)
        TextBlock(
            text="My Book Title",
            x0=100, y0=150, x1=300, y1=180,
            page_height=page_height,
            font_size=10,
            page_num=0,
        ),
        # Actual content on page 0
        TextBlock(
            text="First chapter content here.",
            x0=50, y0=300, x1=550, y1=350,
            page_height=page_height,
            font_size=12,
            page_num=0,
        ),
        # Same repeated header text on page 1
        TextBlock(
            text="My Book Title",
            x0=100, y0=150, x1=300, y1=180,
            page_height=page_height,
            font_size=10,
            page_num=1,
        ),
        # Content on page 1
        TextBlock(
            text="Second chapter content here.",
            x0=50, y0=300, x1=550, y1=350,
            page_height=page_height,
            font_size=12,
            page_num=1,
        ),
        # Same repeated header text on page 2
        TextBlock(
            text="My Book Title",
            x0=100, y0=150, x1=300, y1=180,
            page_height=page_height,
            font_size=10,
            page_num=2,
        ),
        # Content on page 2
        TextBlock(
            text="Third chapter content here.",
            x0=50, y0=300, x1=550, y1=350,
            page_height=page_height,
            font_size=12,
            page_num=2,
        ),
    ]

    parser = PDFParser(use_position_filtering=True)

    with patch.object(
        parser.block_extractor,
        'extract_blocks',
        return_value=(test_blocks, 3)
    ):
        text, page_count = parser._extract_with_position_filtering("/fake/path.pdf")

    # Repeated text should be filtered out (appears on 3 pages = threshold)
    assert "My Book Title" not in text

    # Actual content should be preserved
    assert "First chapter content" in text
    assert "Second chapter content" in text
    assert "Third chapter content" in text
