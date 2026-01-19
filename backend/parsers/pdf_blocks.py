"""Position-aware PDF text block extraction using PyMuPDF."""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional

import yaml

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config" / "settings.yaml"


def _load_pdf_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            settings = yaml.safe_load(f) or {}
        return settings.get("pdf_filtering", {})
    except FileNotFoundError:
        return {}


@dataclass
class TextBlock:
    """A text block with position and font metadata."""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page_height: float
    font_size: float
    page_num: int = 0


ZoneType = Literal["header", "body", "footer"]


class PDFBlockExtractor:
    """Extract and classify text blocks from PDFs by position."""

    def __init__(
        self,
        header_zone_percent: float = 0.10,
        footer_zone_percent: float = 0.10,
        min_body_font_size: float = 9.0,
    ):
        cfg = _load_pdf_config()
        self.header_zone_percent = cfg.get("header_zone_percent", header_zone_percent)
        self.footer_zone_percent = cfg.get("footer_zone_percent", footer_zone_percent)
        self.min_body_font_size = cfg.get("min_body_font_size", min_body_font_size)

    def classify_zone(self, block: TextBlock) -> ZoneType:
        """Classify a block as header, body, or footer based on Y position."""
        relative_y = block.y0 / block.page_height

        if relative_y < self.header_zone_percent:
            return "header"
        elif relative_y > (1 - self.footer_zone_percent):
            return "footer"
        return "body"

    def extract_blocks(self, file_path: str) -> List[TextBlock]:
        """Extract text blocks with coordinates from a PDF file."""
        import fitz  # PyMuPDF

        blocks: List[TextBlock] = []
        doc = fitz.open(file_path)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_height = page.rect.height

            # Get text blocks with position info
            block_list = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

            for b in block_list:
                if b.get("type") != 0:  # Skip non-text blocks (images)
                    continue

                # Extract text and font info from spans
                text_parts = []
                font_sizes = []

                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        text_parts.append(span.get("text", ""))
                        font_sizes.append(span.get("size", 12))

                text = " ".join(text_parts).strip()
                if not text:
                    continue

                avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12

                blocks.append(TextBlock(
                    text=text,
                    x0=b["bbox"][0],
                    y0=b["bbox"][1],
                    x1=b["bbox"][2],
                    y1=b["bbox"][3],
                    page_height=page_height,
                    font_size=avg_font_size,
                    page_num=page_num,
                ))

        doc.close()
        return blocks
