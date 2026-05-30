#!/usr/bin/env python3
"""Phase 73: Known disclosure URL seeding."""
from typing import Any

SEEDS = {
    "688041.SH": [{"title": "Hygon IR Announcements", "url": "https://www.hygon.cn/ir", "source_type": "company_ir_page", "expected_content_type": "html", "allowed_usage": "company_context", "verification_status": "candidate_unverified", "manual_source_note": "Hygon official investor relations page"}],
    "300394.SZ": [{"title": "TFC SZSE Interaction Platform", "url": "", "source_type": "szse_interaction_platform", "expected_content_type": "html", "allowed_usage": "company_context", "verification_status": "manual_fill_required_after_attempt", "why_not_filled": "szse_interaction_platform_url_not_curated", "suggested_lookup_keywords": ["天孚通信 互动易", "300394 互动平台"], "manual_source_note": "Requires manual discovery"}]
}

def seed_known_urls(ticker: str) -> list:
    return SEEDS.get(ticker, [])

def build_seeding_report(tickers=None):
    if tickers is None: tickers = ["688041.SH", "300394.SZ"]
    rows = []
    for t in tickers:
        for e in seed_known_urls(t):
            rows.append({"ticker": t, **e})
    verified = sum(1 for r in rows if r.get("url") and "verified" in r.get("verification_status", ""))
    manual = sum(1 for r in rows if not r.get("url"))
    return {"phase73_known_url_seeding": {"entries_checked": len(rows), "verified_url_entries": verified, "manual_fill_required_remaining": manual, "rows": rows, "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
