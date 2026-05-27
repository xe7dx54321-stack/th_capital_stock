#!/usr/bin/env python3
"""Load text for Phase 28 real IR sources without storing raw files."""

from __future__ import annotations

from typing import Any

from smr_document_text_extraction import extraction_is_usable, is_metadata_only_text, normalize_whitespace
from smr_document_text_extractor import extract_document_text
from smr_paths import normalize_project_path
from smr_text_cache import read_text_cache


def _read_project_text(path_value: str | None, *, limit: int = 12000) -> str:
    if not path_value:
        return ""
    path = normalize_project_path(path_value)
    if not path or not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    marker = "## Extracted Text"
    if marker in text:
        text = text.split(marker, 1)[1]
    elif text.lstrip().startswith("---") and "raw_rel_path:" in text[:2000]:
        return ""
    text = normalize_whitespace(text)
    return "" if is_metadata_only_text(text) else text[:limit]


def load_real_ir_document_text(
    source: dict[str, Any],
    *,
    limit: int = 12000,
    use_text_cache: bool = False,
    extract_text_if_missing: bool = False,
    skip_metadata_only: bool = True,
) -> dict[str, Any]:
    text = ""
    text_source = None
    if use_text_cache:
        cached = read_text_cache(str(source.get("source_id")), source.get("source_url"))
        if cached:
            text = cached
            text_source = "text_cache"
    if not text:
        raw_text = normalize_whitespace(source.get("text") or source.get("text_snippet") or "")
        if raw_text and not (skip_metadata_only and is_metadata_only_text(raw_text)):
            text = raw_text
            text_source = "normalized_text_snippet"
    if not text:
        metadata = source.get("metadata") or {}
        parsed_text = _read_project_text(metadata.get("parsed_text_path") or metadata.get("source_rel_path"), limit=limit)
        if parsed_text:
            text = parsed_text
            text_source = "parsed_text_path"
    extraction = None
    if not text and extract_text_if_missing:
        extraction = extract_document_text(source, write_cache=False)
        if extraction_is_usable(extraction):
            text = extraction.get("text") or ""
            text_source = "document_text_extraction"
    if not text:
        return {
            "source_id": source.get("source_id"),
            "ticker": source.get("ticker"),
            "text": "",
            "text_unavailable": True,
            "text_source": None,
            "reason": (extraction or {}).get("reason") or "no parsed text, text cache, or normalized text snippet available",
            "extraction_status": (extraction or {}).get("extraction_status"),
        }
    return {
        "source_id": source.get("source_id"),
        "ticker": source.get("ticker"),
        "text": text[:limit],
        "text_unavailable": False,
        "text_source": text_source,
        "extraction_status": (extraction or {}).get("extraction_status") or "text_extracted",
        "metadata": {
            "source_url": source.get("source_url"),
            "published_at": source.get("published_at"),
            "real_source": bool(source.get("real_source")),
        },
    }


def attach_real_text_to_source(
    source: dict[str, Any],
    *,
    use_text_cache: bool = False,
    extract_text_if_missing: bool = False,
    skip_metadata_only: bool = True,
) -> dict[str, Any]:
    loaded = load_real_ir_document_text(
        source,
        use_text_cache=use_text_cache,
        extract_text_if_missing=extract_text_if_missing,
        skip_metadata_only=skip_metadata_only,
    )
    if loaded.get("text_unavailable"):
        enriched = dict(source)
        enriched["text_unavailable"] = True
        enriched["text"] = ""
        enriched["text_source"] = loaded.get("text_source")
        enriched["extraction_status"] = loaded.get("extraction_status") or "text_unavailable"
        enriched["text_unavailable_reason"] = loaded.get("reason")
        return enriched
    enriched = dict(source)
    enriched["text"] = loaded.get("text") or ""
    enriched["text_source"] = loaded.get("text_source")
    enriched["text_unavailable"] = False
    enriched["extraction_status"] = loaded.get("extraction_status") or "text_extracted"
    return enriched


def attach_real_text_to_sources(
    sources: list[dict[str, Any]],
    *,
    use_text_cache: bool = False,
    extract_text_if_missing: bool = False,
    skip_metadata_only: bool = True,
) -> list[dict[str, Any]]:
    return [
        attach_real_text_to_source(
            source,
            use_text_cache=use_text_cache,
            extract_text_if_missing=extract_text_if_missing,
            skip_metadata_only=skip_metadata_only,
        )
        for source in sources
    ]
