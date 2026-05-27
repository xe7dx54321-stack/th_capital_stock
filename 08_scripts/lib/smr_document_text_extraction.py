#!/usr/bin/env python3
"""Phase 29 document text extraction schema and quality gates."""

from __future__ import annotations

from typing import Any


DOCUMENT_TYPES = {"pdf", "html", "plain_text", "local_text", "metadata_only", "unknown"}
EXTRACTION_STATUSES = {
    "text_extracted",
    "text_too_short",
    "metadata_only",
    "scanned_pdf_needs_ocr",
    "table_only",
    "unsupported_format",
    "download_unavailable",
    "extraction_failed",
}
ACTIVE_TEXT_STATUSES = {"text_extracted"}
MIN_TEXT_CHARS = 220


def normalize_whitespace(text: str | None) -> str:
    lines = [line.strip() for line in str(text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    cleaned = []
    previous_blank = False
    for line in lines:
        if not line:
            if not previous_blank:
                cleaned.append("")
            previous_blank = True
            continue
        cleaned.append(" ".join(line.split()))
        previous_blank = False
    return "\n".join(cleaned).strip()


def is_metadata_only_text(text: str | None) -> bool:
    text = normalize_whitespace(text)
    if not text:
        return False
    labels = ("证券代码", "证券简称", "公告标题", "公告日期", "公告类型", "披露板块", "原始文件")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    metadata_lines = [line for line in lines if any(line.startswith(label) for label in labels)]
    return len(text) < 700 and len(metadata_lines) >= max(3, len(lines) - 1)


def detect_document_type(source: dict[str, Any]) -> str:
    metadata = source.get("metadata") or {}
    content_type = str(metadata.get("content_type") or "").lower()
    url = str(source.get("source_url") or "").lower()
    path = str(source.get("local_file_path") or metadata.get("raw_rel_path") or metadata.get("parsed_text_path") or "").lower()
    if source.get("document_type") in DOCUMENT_TYPES:
        return str(source.get("document_type"))
    if "pdf" in content_type or url.endswith(".pdf") or path.endswith(".pdf"):
        return "pdf"
    if "html" in content_type or url.endswith((".htm", ".html")) or path.endswith((".htm", ".html")):
        return "html"
    if source.get("text") or source.get("text_snippet"):
        return "plain_text"
    if path.endswith((".txt", ".md")):
        return "local_text"
    return "unknown"


def make_document_text_extraction(
    *,
    source: dict[str, Any],
    document_type: str,
    extraction_status: str,
    text: str = "",
    page_count: int | None = None,
    sections_detected: list[str] | None = None,
    text_cache_path: str | None = None,
    quality_flags: list[str] | None = None,
    limitations: list[str] | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    document_type = document_type if document_type in DOCUMENT_TYPES else "unknown"
    extraction_status = extraction_status if extraction_status in EXTRACTION_STATUSES else "extraction_failed"
    text = normalize_whitespace(text)
    if extraction_status == "text_extracted" and is_metadata_only_text(text):
        extraction_status = "metadata_only"
        reason = reason or "text contains only source metadata"
    if extraction_status == "text_extracted" and len(text) < MIN_TEXT_CHARS:
        extraction_status = "text_too_short"
        reason = reason or "clean text is shorter than minimum extraction threshold"
    limitations = list(limitations or [])
    if extraction_status == "extraction_failed" and reason and reason not in limitations:
        limitations.append(reason)
    return {
        "source_id": source.get("source_id"),
        "ticker": source.get("ticker"),
        "source_type": source.get("source_type"),
        "document_type": document_type,
        "source_url": source.get("source_url"),
        "published_at": source.get("published_at"),
        "extraction_status": extraction_status,
        "text_char_count": len(text),
        "page_count": page_count,
        "sections_detected": sections_detected or [],
        "text_cache_path": text_cache_path,
        "raw_content_saved": False,
        "quality_flags": quality_flags or [],
        "limitations": limitations,
        "reason": reason,
        "text": text,
    }


def extraction_is_usable(result: dict[str, Any]) -> bool:
    return result.get("extraction_status") in ACTIVE_TEXT_STATUSES and bool(result.get("text"))
