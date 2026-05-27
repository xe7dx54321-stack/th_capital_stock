#!/usr/bin/env python3
"""Clean text cache for Phase 29 extracted IR documents."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from smr_document_text_extraction import normalize_whitespace
from smr_paths import project_path, relative_to_project
from smr_wiki import now_ts


TEXT_CACHE_DIR = project_path("08_data", "generated", "text_cache")


def build_text_cache_key(source_id: str, source_url: str | None) -> str:
    digest = hashlib.sha256(f"{source_id}|{source_url or ''}".encode("utf-8")).hexdigest()[:20]
    safe_source = "".join(ch if ch.isalnum() else "_" for ch in str(source_id or "unknown").lower()).strip("_")
    return f"{safe_source}_{digest}"


def _cache_paths(source_id: str, source_url: str | None) -> tuple[Path, Path]:
    key = build_text_cache_key(source_id, source_url)
    return TEXT_CACHE_DIR / f"{key}.text_cache.txt", TEXT_CACHE_DIR / f"{key}.text_cache.json"


def write_text_cache(source_meta: dict[str, Any], text: str) -> dict[str, Any]:
    clean = normalize_whitespace(text)
    TEXT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    text_path, meta_path = _cache_paths(str(source_meta.get("source_id")), source_meta.get("source_url"))
    text_path.write_text(clean, encoding="utf-8")
    payload = {
        "source_id": source_meta.get("source_id"),
        "ticker": source_meta.get("ticker"),
        "source_url": source_meta.get("source_url"),
        "text_hash": hashlib.sha256(clean.encode("utf-8")).hexdigest(),
        "text_char_count": len(clean),
        "created_at": now_ts(),
        "text_path": relative_to_project(text_path),
        "raw_content_saved": False,
    }
    meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def read_text_cache(source_id: str, source_url: str | None = None) -> str | None:
    if not source_id:
        return None
    if source_url is not None:
        text_path, _ = _cache_paths(source_id, source_url)
        if text_path.exists():
            return text_path.read_text(encoding="utf-8", errors="replace")
    if not TEXT_CACHE_DIR.exists():
        return None
    safe_source = "".join(ch if ch.isalnum() else "_" for ch in str(source_id).lower()).strip("_")
    matches = sorted(TEXT_CACHE_DIR.glob(f"{safe_source}_*.text_cache.txt"))
    if not matches:
        return None
    return matches[0].read_text(encoding="utf-8", errors="replace")


def summarize_text_cache() -> dict[str, Any]:
    if not TEXT_CACHE_DIR.exists():
        return {"cache_dir": relative_to_project(TEXT_CACHE_DIR), "cache_entries": 0, "total_text_chars": 0}
    entries = []
    for meta_path in TEXT_CACHE_DIR.glob("*.text_cache.json"):
        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        entries.append(payload)
    return {
        "cache_dir": relative_to_project(TEXT_CACHE_DIR),
        "cache_entries": len(entries),
        "total_text_chars": sum(int(item.get("text_char_count") or 0) for item in entries),
        "raw_content_saved": False,
    }
