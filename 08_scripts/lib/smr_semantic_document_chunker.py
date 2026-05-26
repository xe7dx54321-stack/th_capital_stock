#!/usr/bin/env python3
"""Phase 27 document chunking for semantic evidence extraction."""

from __future__ import annotations

import re
from typing import Any


def _split_qa(text: str) -> list[str]:
    parts = re.split(r"(?=问[:：])", text)
    return [part.strip() for part in parts if part.strip()]


def chunk_document(source: dict[str, Any], *, max_chars: int = 900) -> list[dict[str, Any]]:
    text = str(source.get("text") or "").strip()
    if not text:
        return []
    segments = _split_qa(text) if "问" in text and "答" in text else [part.strip() for part in re.split(r"\n\s*\n|。", text) if part.strip()]
    chunks: list[dict[str, Any]] = []
    buffer = ""
    for segment in segments:
        segment = segment if segment.endswith("。") else f"{segment}。"
        if buffer and len(buffer) + len(segment) > max_chars:
            chunks.append(_make_chunk(source, buffer, len(chunks)))
            buffer = segment
        else:
            buffer = f"{buffer}\n{segment}".strip()
    if buffer:
        chunks.append(_make_chunk(source, buffer, len(chunks)))
    return chunks


def _make_chunk(source: dict[str, Any], text: str, index: int) -> dict[str, Any]:
    return {
        "source_id": source.get("source_id"),
        "chunk_id": f"chunk_{index + 1:04d}",
        "ticker": source.get("ticker"),
        "source_type": source.get("source_type") or "unknown",
        "section_title": source.get("title") or "unknown",
        "text": text,
        "char_count": len(text),
        "metadata": {
            "published_at": source.get("published_at"),
            "source_url": source.get("source_url"),
            "title": source.get("title"),
        },
    }


def chunk_sources(sources: list[dict[str, Any]], *, max_chars: int = 900) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for source in sources:
        chunks.extend(chunk_document(source, max_chars=max_chars))
    return chunks
