#!/usr/bin/env python3
"""Phase 27 document chunking for semantic evidence extraction."""

from __future__ import annotations

import re
from typing import Any

from smr_ir_section_splitter import split_ir_sections


def _split_qa(text: str) -> list[str]:
    parts = re.split(r"(?=问[:：])", text)
    return [part.strip() for part in parts if part.strip()]


def chunk_document(source: dict[str, Any], *, max_chars: int = 900) -> list[dict[str, Any]]:
    text = str(source.get("text") or "").strip()
    if not text:
        return []
    section_payload = split_ir_sections(source)
    sections = section_payload.get("sections") or []
    if sections:
        chunks: list[dict[str, Any]] = []
        for section in sections:
            chunks.extend(_chunk_section(source, section, len(chunks), max_chars=max_chars))
        return chunks
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


def _chunk_section(source: dict[str, Any], section: dict[str, Any], start_index: int, *, max_chars: int) -> list[dict[str, Any]]:
    text = str(section.get("text") or "").strip()
    if not text:
        return []
    segments = _split_qa(text) if "问" in text and "答" in text else [part.strip() for part in re.split(r"\n\s*\n|。", text) if part.strip()]
    chunks: list[dict[str, Any]] = []
    buffer = ""
    for segment in segments:
        segment = segment if segment.endswith("。") else f"{segment}。"
        if buffer and len(buffer) + len(segment) > max_chars:
            chunks.append(_make_chunk(source, buffer, start_index + len(chunks), section=section))
            buffer = segment
        else:
            buffer = f"{buffer}\n{segment}".strip()
    if buffer:
        chunks.append(_make_chunk(source, buffer, start_index + len(chunks), section=section))
    return chunks


def _make_chunk(source: dict[str, Any], text: str, index: int, *, section: dict[str, Any] | None = None) -> dict[str, Any]:
    section = section or {}
    return {
        "source_id": source.get("source_id"),
        "chunk_id": f"chunk_{index + 1:04d}",
        "ticker": source.get("ticker"),
        "source_type": source.get("source_type") or "unknown",
        "section_title": section.get("title") or source.get("title") or "unknown",
        "text": text,
        "char_count": len(text),
        "metadata": {
            "published_at": source.get("published_at"),
            "source_url": source.get("source_url"),
            "title": source.get("title"),
            "real_source": bool(source.get("real_source")),
            "mock_source": bool(source.get("mock_source")),
            "source_quality": source.get("source_quality"),
            "section_id": section.get("section_id"),
            "section_type": section.get("section_type"),
            "section_priority": section.get("priority"),
            "text_source": source.get("text_source"),
            "extraction_status": source.get("extraction_status"),
        },
    }


def chunk_sources(sources: list[dict[str, Any]], *, max_chars: int = 900) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for source in sources:
        chunks.extend(chunk_document(source, max_chars=max_chars))
    return chunks
