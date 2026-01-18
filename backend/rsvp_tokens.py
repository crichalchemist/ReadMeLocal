from __future__ import annotations

import re

PUNCTUATION = {",", ";", ":", ".", "!", "?"}


def split_paragraphs(text: str) -> list[str]:
    chunks = re.split(r"\n\s*\n+", text.strip())
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def tokenize_paragraphs(paragraphs: list[str]) -> list[dict]:
    tokens: list[dict] = []
    word_re = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)?|[.,;:!?]")
    for p_index, paragraph in enumerate(paragraphs):
        for match in word_re.findall(paragraph):
            if match in PUNCTUATION and tokens:
                tokens[-1]["punct"] = match
                if match in {".", "!", "?"}:
                    tokens[-1]["sentence_end"] = True
                continue
            tokens.append(
                {
                    "text": match,
                    "punct": "",
                    "sentence_end": False,
                    "paragraph_index": p_index,
                }
            )
    return tokens
