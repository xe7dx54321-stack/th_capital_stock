#!/usr/bin/env python3
"""Phase 73: Company IR URL seeding."""
from typing import Any

SEEDS = {
    "688041.SH": {"official_site": "https://www.hygon.cn", "ir_page": "https://www.hygon.cn/ir", "announcement_page": "", "source_confidence": "curated_from_company_domain", "verification_status": "candidate_unverified", "note": "Hygon official site and IR page candidates"},
    "300394.SZ": {"official_site": "", "ir_page": "", "announcement_page": "", "source_confidence": "unknown", "verification_status": "manual_fill_required_after_attempt", "why_not_filled": "no_verified_public_ir_page_url_in_curated_candidates", "suggested_lookup_keywords": ["天孚通信 投资者关系", "天孚通信 公告", "天孚通信 IR", "天孚通信 300394 互动平台"], "note": "TFC official site unverified"}
}

def seed_company_ir(ticker: str) -> dict[str, Any]:
    s = SEEDS.get(ticker, {})
    if not s: return {"ticker": ticker, "verification_status": "not_found", "mock_used": False, "fixture_used": False}
    return {"ticker": ticker, **s, "mock_used": False, "fixture_used": False}

def build_seeding_report(tickers=None):
    if tickers is None: tickers = ["688041.SH", "300394.SZ"]
    rows = [seed_company_ir(t) for t in tickers]
    url_seeded = sum(1 for r in rows if r.get("official_site") or r.get("ir_page"))
    manual = sum(1 for r in rows if not r.get("official_site") and not r.get("ir_page"))
    return {"phase73_company_ir_url_seeding": {"tickers_checked": len(tickers), "url_seeded": url_seeded, "manual_fill_required_remaining": manual, "rows": rows, "mock_used": False, "fixture_used": False}}
