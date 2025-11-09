"""
Content filtering utilities shared between the FastAPI app and document parsers.
Implements the smart filtering pipeline described in the revised MVP plan.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "settings.yaml"


def _load_settings() -> Dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError:
        return {}


SETTINGS = _load_settings()


class ContentFilter:
    """
    Phase 3: Smart Content Parsing utilities.

    Implements a pipeline with steps controlled by config under SETTINGS['content_filtering'].
    """

    CHAPTER_REGEX = re.compile(
        r"^\s*(chapter\s+[0-9ivxlcdm]+\b|prologue\b|part\s+[0-9ivxlcdm]+\b|book\s+[0-9ivxlcdm]+\b)",
        re.IGNORECASE,
    )
    PAGE_NUMBER_REGEX = re.compile(r"^\s*(page\s+\d+\s*(of\s*\d+)?|\d+)\s*$", re.IGNORECASE)
    INLINE_FOOTNOTE_REGEX = re.compile(r"\[(\d+|[ivxlcdm]+)\]")
    FOOTNOTE_LINE_REGEX = re.compile(r"^\s*(\[(\d+|[ivxlcdm]+)\]|\d+[\.)])\s+")

    def __init__(self, settings: Optional[Dict] = None):
        cfg_source = settings or SETTINGS
        if cfg_source and "content_filtering" in cfg_source:
            cfg = cfg_source.get("content_filtering") or {}
        else:
            cfg = cfg_source or {}

        self.skip_frontmatter = bool(cfg.get("skip_frontmatter", True))
        self.skip_page_numbers = bool(cfg.get("skip_page_numbers", True))
        self.skip_footnotes = bool(cfg.get("skip_footnotes", True))
        self.skip_headers_footers = bool(cfg.get("skip_headers_footers", True))
        self.frontmatter_skip_percent = float(cfg.get("frontmatter_skip_percent", 0.05))
        self.repeat_threshold = int(cfg.get("repeat_threshold", 3))

    def filter_text(self, text: str) -> str:
        if not text:
            return text
        lines = text.splitlines()
        # Frontmatter skip: find first chapter-like marker
        if self.skip_frontmatter:
            start_idx = self._find_content_start(lines)
            if start_idx is None:
                # Fallback: skip first N% of characters
                n_chars = int(len(text) * self.frontmatter_skip_percent)
                text_after = text[n_chars:]
                lines = text_after.splitlines()
            else:
                lines = lines[start_idx:]

        # Remove headers/footers by frequency
        if self.skip_headers_footers:
            lines = self._remove_repeated_lines(lines)

        # Remove page numbers lines
        if self.skip_page_numbers:
            lines = [ln for ln in lines if not self.PAGE_NUMBER_REGEX.match(ln.strip())]

        # Remove footnote lines and inline refs
        joined = "\n".join(lines)
        if self.skip_footnotes:
            # Remove inline [n] markers
            joined = self.INLINE_FOOTNOTE_REGEX.sub("", joined)
            # Remove lines that look like footnotes
            new_lines = []
            for ln in joined.splitlines():
                if self.FOOTNOTE_LINE_REGEX.match(ln.strip()):
                    # Likely a footnote; drop if relatively short to avoid killing numbered sections
                    if len(ln.strip()) <= 200:
                        continue
                new_lines.append(ln)
            joined = "\n".join(new_lines)
        return joined

    def _find_content_start(self, lines: List[str]) -> Optional[int]:
        for idx, ln in enumerate(lines[:1000]):  # only scan first ~1000 lines for performance
            if self.CHAPTER_REGEX.search(ln):
                return idx
        return None

    def _remove_repeated_lines(self, lines: List[str]) -> List[str]:
        freq: Dict[str, int] = {}
        norm_map: Dict[int, str] = {}
        for i, ln in enumerate(lines):
            norm = ln.strip().lower()
            norm = re.sub(r"\s+", " ", norm)
            norm_map[i] = norm
            if not norm:
                continue
            # ignore too long content lines
            if len(norm) > 80:
                continue
            freq[norm] = freq.get(norm, 0) + 1
        repeated = {s for s, c in freq.items() if c > self.repeat_threshold}
        if not repeated:
            return lines
        out: List[str] = []
        for i, ln in enumerate(lines):
            if norm_map.get(i, "") in repeated:
                continue
            out.append(ln)
        return out
