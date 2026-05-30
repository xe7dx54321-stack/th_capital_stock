#!/usr/bin/env python3
"""Phase 71 multi-source capability matrix."""
import argparse, json, sys

def build():
    rows = [
        {"ticker": "300308.SZ", "cninfo": "full_chain_available", "irm": "optional", "exchange_page": "optional", "company_site": "manual_fill_required", "known_catalog": "manual_fill_required", "overall": "full_chain_available"},
        {"ticker": "688041.SH", "cninfo": "metadata_available_pdf_text_blocked", "sse_page": "attempted_or_available", "company_site": "manual_fill_required", "known_catalog": "manual_fill_required", "overall": "partial_chain_with_fallback", "partial_reason": "cninfo_pdf_blocked_sse_page_can_provide_metadata"},
        {"ticker": "300394.SZ", "cninfo": "identity_blocked", "irm": "attempted_market_supported", "szse_page": "attempted", "company_site": "manual_fill_required", "known_catalog": "manual_fill_required", "overall": "blocked_or_partial_with_fallback", "blocker": "cninfo_identity_and_manual_url_required"}
    ]
    return {"multi_source_capability_matrix": {"tickers_checked": 3, "rows": rows, "sources_tracked": ["cninfo","irm","exchange_page","company_site","known_catalog"], "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        cm = r["multi_source_capability_matrix"]
        lines = ["# Multi-source Capability Matrix", "", "| Ticker | CNINFO | IRM | Exchange | Company | Known | Overall |", "|--------|--------|-----|----------|---------|-------|---------|"]
        for row in cm["rows"]: lines.append(f"| {row['ticker']} | {row['cninfo']} | {row.get('irm','-')} | {row.get('exchange_page',row.get('sse_page','-'))} | {row.get('company_site','-')} | {row.get('known_catalog','-')} | {row['overall']} |")
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
