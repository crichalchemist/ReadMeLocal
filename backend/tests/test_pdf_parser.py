"""Tests for PDF parser with position-aware filtering."""
import sys
import pytest
from unittest.mock import MagicMock, patch

# Mock fitz module before importing PDFParser
mock_fitz = MagicMock()
sys.modules['fitz'] = mock_fitz

from backend.parsers.pdf_parser import PDFParser


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
