#!/usr/bin/env python3
"""Extract clean text from real IR PDF/HTML/text sources without saving raw files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from smr_document_text_extraction import (
    detect_document_type,
    is_metadata_only_text,
    make_document_text_extraction,
    normalize_whitespace,
)
from smr_ir_section_splitter import split_ir_sections
from smr_paths import normalize_project_path
from smr_text_cache import write_text_cache


def _metadata(source: dict[str, Any]) -> dict[str, Any]:
    value = source.get("metadata") or {}
    return value if isinstance(value, dict) else {}


def resolve_local_document_path(source: dict[str, Any]) -> Path | None:
    metadata = _metadata(source)
    candidates = [
        source.get("local_file_path"),
        metadata.get("raw_rel_path"),
        metadata.get("parsed_text_path"),
        metadata.get("source_rel_path"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = normalize_project_path(candidate)
        if path and path.exists():
            return path
    parsed = metadata.get("parsed_text_path") or metadata.get("source_rel_path")
    if parsed:
        parsed_path = normalize_project_path(parsed)
        if parsed_path and parsed_path.exists():
            try:
                raw = parsed_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                raw = ""
            raw_rel = _extract_frontmatter_value(raw, "raw_rel_path")
            if raw_rel:
                raw_path = normalize_project_path(raw_rel)
                if raw_path and raw_path.exists():
                    return raw_path
    return None


def _extract_frontmatter_value(text: str, key: str) -> str | None:
    for line in text.splitlines()[:80]:
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def _extract_markdown_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    marker = "## Extracted Text"
    if marker in text:
        text = text.split(marker, 1)[1]
    elif text.lstrip().startswith("---") and "raw_rel_path:" in text[:2000]:
        text = ""
    return normalize_whitespace(text)


def _extract_pdf_text(path: Path) -> tuple[str, int]:
    try:
        import fitz  # type: ignore
    except Exception:  # pragma: no cover - fallback depends on local env
        fitz = None
    if fitz is not None:
        with fitz.open(str(path)) as doc:
            pages = [page.get_text("text") for page in doc]
            return normalize_whitespace("\n\n".join(pages)), len(doc)
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return "", 0
    reader = PdfReader(str(path))
    return normalize_whitespace("\n\n".join(page.extract_text() or "" for page in reader.pages)), len(reader.pages)


def _extract_html_text(path: Path) -> str:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return normalize_whitespace(soup.get_text("\n"))


def _quality_flags(text: str) -> list[str]:
    flags = []
    if text:
        flags.append("has_text")
    if "问" in text and "答" in text:
        flags.append("has_qa_structure")
    if any(term in text for term in ("产能", "光模块", "光器件", "客户", "毛利", "价格", "需求")):
        flags.append("has_supply_chain_terms")
    return flags


def detect_sections(text: str, source: dict[str, Any]) -> list[str]:
    enriched = dict(source)
    enriched["text"] = text
    return list(dict.fromkeys(section.get("section_type") for section in split_ir_sections(enriched).get("sections") or [] if section.get("section_type")))


def extract_document_text(source: dict[str, Any], *, write_cache: bool = False) -> dict[str, Any]:
    document_type = detect_document_type(source)
    text = normalize_whitespace(source.get("text") or source.get("text_snippet"))
    page_count = None
    local_path = resolve_local_document_path(source)
    try:
        if local_path:
            suffix = local_path.suffix.lower()
            if suffix == ".pdf":
                document_type = "pdf"
                text, page_count = _extract_pdf_text(local_path)
            elif suffix in {".htm", ".html"}:
                document_type = "html"
                text = _extract_html_text(local_path)
            elif suffix in {".txt", ".md"} and not text:
                document_type = "local_text"
                text = _extract_markdown_body(local_path)
        elif not text:
            return make_document_text_extraction(
                source=source,
                document_type=document_type,
                extraction_status="download_unavailable" if source.get("source_url") else "unsupported_format",
                reason="no local file path or existing text available",
            )
    except Exception as exc:  # pragma: no cover - defensive for malformed PDFs
        return make_document_text_extraction(
            source=source,
            document_type=document_type,
            extraction_status="extraction_failed",
            page_count=page_count,
            reason=f"{type(exc).__name__}: {exc}",
        )
    text = normalize_whitespace(text)
    if is_metadata_only_text(text):
        status = "metadata_only"
    elif not text and document_type == "pdf":
        status = "scanned_pdf_needs_ocr"
    elif not text:
        status = "extraction_failed"
    elif len(text) < 220:
        status = "text_too_short"
    elif _looks_table_only(text):
        status = "table_only"
    else:
        status = "text_extracted"
    cache_payload = None
    if write_cache and status == "text_extracted":
        cache_payload = write_text_cache(source, text)
    result = make_document_text_extraction(
        source=source,
        document_type=document_type,
        extraction_status=status,
        text=text,
        page_count=page_count,
        sections_detected=detect_sections(text, source) if status == "text_extracted" else [],
        text_cache_path=(cache_payload or {}).get("text_path"),
        quality_flags=_quality_flags(text) if status == "text_extracted" else [],
        limitations=[] if status == "text_extracted" else [_status_reason(status)],
        reason=None if status == "text_extracted" else _status_reason(status),
    )
    return result


def _looks_table_only(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 5:
        return False
    numericish = sum(1 for line in lines if len(re.findall(r"\d", line)) > max(5, len(line) // 3))
    return numericish / max(1, len(lines)) > 0.75


def _status_reason(status: str) -> str:
    return {
        "metadata_only": "text contains only source metadata",
        "text_too_short": "text layer is too short for semantic extraction",
        "scanned_pdf_needs_ocr": "pdf text layer is empty; OCR is not enabled by default",
        "table_only": "extracted text appears table-only",
        "extraction_failed": "document text extraction failed",
    }.get(status, status)
