#!/usr/bin/env python3
"""Load text for Phase 28 real IR sources without storing raw files."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _is_metadata_only_text(text: str) -> bool:
    labels = ("证券代码", "证券简称", "公告标题", "公告日期", "公告类型", "披露板块", "原始文件")
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    return bool(lines) and len(text) < 600 and all(any(line.startswith(label) for label in labels) for line in lines)


def _read_project_text(path_value: str | None, *, limit: int = 12000) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.is_absolute():
        path = Path.cwd() / path
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    marker = "## Extracted Text"
    if marker in text:
        text = text.split(marker, 1)[1]
    elif text.lstrip().startswith("---") and "raw_rel_path:" in text[:2000]:
        return ""
    text = text.strip()
    if _is_metadata_only_text(text):
        return ""
    return text[:limit]


def load_real_ir_document_text(source: dict[str, Any], *, limit: int = 12000) -> dict[str, Any]:
    text = str(source.get("text") or source.get("text_snippet") or "").strip()
    text_source = "normalized_text_snippet" if text else None
    metadata = source.get("metadata") or {}
    if not text:
        text = _read_project_text(metadata.get("parsed_text_path") or metadata.get("source_rel_path"), limit=limit)
        text_source = "parsed_text_path" if text else None
    if not text:
        return {
            "source_id": source.get("source_id"),
            "ticker": source.get("ticker"),
            "text": "",
            "text_unavailable": True,
            "text_source": None,
            "reason": "no parsed text or normalized text snippet available",
        }
    return {
        "source_id": source.get("source_id"),
        "ticker": source.get("ticker"),
        "text": text[:limit],
        "text_unavailable": False,
        "text_source": text_source,
        "metadata": {
            "source_url": source.get("source_url"),
            "published_at": source.get("published_at"),
            "real_source": bool(source.get("real_source")),
        },
    }


def attach_real_text_to_source(source: dict[str, Any]) -> dict[str, Any]:
    loaded = load_real_ir_document_text(source)
    if loaded.get("text_unavailable"):
        enriched = dict(source)
        enriched["text_unavailable"] = True
        enriched["text"] = ""
        return enriched
    enriched = dict(source)
    enriched["text"] = loaded.get("text") or ""
    enriched["text_source"] = loaded.get("text_source")
    enriched["text_unavailable"] = False
    return enriched


def attach_real_text_to_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [attach_real_text_to_source(source) for source in sources]
