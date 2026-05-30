#!/usr/bin/env python3
"""Phase 71: Fallback text fetcher."""
import hashlib
from typing import Any

def fetch_fallback_texts(irm_report: dict = None, exchange_report: dict = None, company_ir_report: dict = None) -> dict[str, Any]:
    """Collect usable texts from fallback sources."""
    rows = []

    # From IRM
    if irm_report:
        ir = irm_report.get("irm_interaction_report", irm_report)
        for row in ir.get("rows", []):
            ticker = row.get("ticker", "")
            for item in row.get("items", []):
                answer = item.get("answer", "")
                question = item.get("question", "")
                if answer and len(answer) >= 50:
                    text = f"Q: {question}\nA: {answer}"
                    rows.append({"ticker": ticker, "source_type": "irm", "text_status": "usable_text" if len(text) >= 100 else "short_text", "text_length": len(text), "text_hash": "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], "allowed_usage": "management_commentary"})

    # From exchange disclosure - metadata-only, not usable text
    if exchange_report:
        er = exchange_report.get("exchange_disclosure_report", exchange_report)
        for row in er.get("rows", []):
            if row.get("metadata_found", 0) > 0:
                rows.append({"ticker": row.get("ticker", ""), "source_type": "exchange_page", "text_status": "metadata_only_not_text", "text_length": 0, "text_hash": "", "allowed_usage": "metadata_only", "note": "exchange_metadata_available_but_text_extraction_needs_pdf_or_page_fetch"})

    # From company IR page
    if company_ir_report:
        cr = company_ir_report.get("company_ir_page_report", company_ir_report)
        for row in cr.get("rows", []):
            if row.get("status") == "manual_fill_required":
                rows.append({"ticker": row.get("ticker", ""), "source_type": "company_site", "text_status": "manual_fill_required", "text_length": 0, "text_hash": "", "allowed_usage": "not_available"})

    usable = sum(1 for r in rows if r.get("text_status") == "usable_text")
    return {"fallback_text_fetch_report": {"tickers_checked": 3, "texts_fetched": len(rows), "texts_normalized": usable, "texts_usable_for_evidence": usable, "rows": rows, "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
