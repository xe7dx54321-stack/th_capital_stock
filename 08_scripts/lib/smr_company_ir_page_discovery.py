#!/usr/bin/env python3
"""Phase 71: Company IR page discovery."""
import json
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "company_ir_page_candidates.json"

def load_company_config() -> dict[str, Any]:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"companies": []}

def discover_ir_page(ticker: str) -> dict[str, Any]:
    companies = load_company_config().get("companies", [])
    for c in companies:
        if c["ticker"] == ticker:
            if c.get("status") == "manual_fill_required":
                return {"ticker": ticker, "company_name": c.get("company_name", ""), "ir_page_found": False, "status": "manual_fill_required", "official_site": c.get("official_site", ""), "ir_page": c.get("ir_page", ""), "mock_used": False, "fixture_used": False}
            if c.get("ir_page"):
                return {"ticker": ticker, "company_name": c.get("company_name", ""), "ir_page_found": True, "status": "url_available_not_fetched", "ir_page": c.get("ir_page", ""), "mock_used": False, "fixture_used": False}
    return {"ticker": ticker, "ir_page_found": False, "status": "not_in_config", "mock_used": False, "fixture_used": False}

def build_company_ir_report(tickers: list = None) -> dict[str, Any]:
    if tickers is None: tickers = ["300308.SZ", "688041.SH", "300394.SZ"]
    rows = [discover_ir_page(t) for t in tickers]
    found = sum(1 for r in rows if r.get("ir_page_found"))
    manual = sum(1 for r in rows if r.get("status") == "manual_fill_required")
    return {"company_ir_page_report": {"tickers_checked": len(tickers), "ir_pages_found": found, "manual_fill_required": manual, "rows": rows, "mock_used": False, "fixture_used": False}}
