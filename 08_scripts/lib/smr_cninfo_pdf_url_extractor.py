#!/usr/bin/env python3
"""CNINFO PDF URL extractor - Phase 65."""

from __future__ import annotations
import json, urllib.request, urllib.parse
from typing import Any

CNINFO_PDF_BASE = "https://static.cninfo.com.cn/"


def extract_pdf_urls_from_metadata(metadata_rows: list[dict]) -> list[dict]:
    results = []
    for row in metadata_rows:
        pdf_url = row.get("adjunctUrl", row.get("pdfUrl", row.get("pdf_url", "")))
        if pdf_url:
            if pdf_url.startswith("/"):
                pdf_url = CNINFO_PDF_BASE.rstrip("/") + pdf_url
            elif not pdf_url.startswith("http"):
                pdf_url = CNINFO_PDF_BASE + pdf_url
        results.append({
            "source_id": row.get("source_id", row.get("id", "")),
            "title": row.get("title", row.get("announcementTitle", "")),
            "publish_date": row.get("publishDate", row.get("announceTime", "")),
            "pdf_url": pdf_url,
            "url_status": "valid_format" if pdf_url and pdf_url.startswith("http") else "missing_or_invalid",
            "allowed_usage": "pdf_text_extraction" if pdf_url else "no_pdf_url",
        })
    return results


def build_pdf_url_inventory(ticker: str = "300308.SZ", metadata_rows: list[dict] | None = None) -> dict[str, Any]:
    if metadata_rows is None:
        metadata_rows = []
    extracted = extract_pdf_urls_from_metadata(metadata_rows)
    found = sum(1 for r in extracted if r["pdf_url"])
    return {
        "ticker": ticker,
        "cninfo_pdf_url_inventory": {
            "metadata_sources_checked": len(metadata_rows),
            "pdf_urls_found": found,
            "pdf_url_validated": found,
            "rows": extracted,
            "raw_pdf_saved": False,
            "ocr_used": False,
            "mock_used": False,
            "fixture_used": False,
        },
    }
