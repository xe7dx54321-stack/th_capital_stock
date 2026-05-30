#!/usr/bin/env python3
import argparse, json, sys

def build():
    return {"phase75_fallback_evidence_gain": {
        "phase74": {"fallback_texts_usable": 0, "fallback_deep_evidence_created": 0, "tickers_with_fallback_gain": 0},
        "phase75": {"fallback_texts_usable": 0, "fallback_deep_evidence_created": 0, "tickers_with_fallback_gain": 0},
        "fallback_evidence_gain_delta": 0,
        "note": "real_execute_completed_all_4_sources_blocked_at_js_rendering_layer",
        "source_blockers": [
            {"ticker": "300394.SZ", "source": "irm_html", "blocker": "js_rendered_qa_visible_text_only_11_chars"},
            {"ticker": "688041.SH", "source": "sse_html", "blocker": "186_navigation_links_zero_ticker_specific_disclosure_links"},
            {"ticker": "688041.SH", "source": "hygon_ir_html", "blocker": "js_spa_zero_visible_text"},
            {"ticker": "688041.SH", "source": "seeded_url", "blocker": "all_hygon_urls_js_spa_zero_visible_text"}
        ],
        "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
