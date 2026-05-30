#!/usr/bin/env python3
import argparse, json, sys

def build():
    rows = [
        {"ticker": "300308.SZ", "cninfo": "full_chain_available", "fallback": "optional", "overall": "full_chain_available"},
        {"ticker": "688041.SH", "cninfo": "metadata_available_pdf_text_blocked",
         "sse_html": "links_are_navigation_boilerplate_zero_disclosure_links",
         "company_ir_html": "hygon_cn_js_spa_zero_visible_text",
         "known_catalog": "seeded_but_all_js_spa",
         "overall": "blocked_at_js_rendering_layer",
         "blocker": "all_html_sources_require_js_rendering"},
        {"ticker": "300394.SZ", "cninfo": "identity_blocked",
         "irm_html": "js_rendered_qa_only_11_chars_visible_text",
         "szse_html": "not_yet_attempted",
         "company_site": "manual_or_available",
         "overall": "blocked_at_irm_js_rendering",
         "blocker": "irm_html_requires_js_execution"}
    ]
    return {"phase75_multi_source_capability_matrix": {"tickers_checked": 3, "tickers_with_fallback_text": 0,
        "tickers_with_fallback_evidence": 0, "rows": rows,
        "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
