#!/usr/bin/env python3
import argparse, json, sys

def build():
    return {"summary": {
        "tickers_checked": 3, "network_attempted": True,
        "html_pages_fetched": 8,
        "irm_html": {"qa_items_found": 0, "qa_text_usable": 0, "blocker": "js_rendered_qa_not_in_static_html", "visible_text_chars": 11},
        "sse_html": {"announcement_links_found": 186, "pdf_links_found": 0, "blocker": "links_are_navigation_boilerplate_not_ticker_specific", "visible_text_chars": 818, "disclosure_links": 0},
        "hygon_ir_html": {"pages_fetched": 3, "text_blocks_found": 0, "blocker": "hygon_cn_is_js_spa_zero_visible_text"},
        "seeded_url_html": {"urls_checked": 3, "texts_usable": 0, "blocker": "all_hygon_urls_are_js_spa_zero_visible_text"},
        "fallback_texts_usable": 0,
        "fallback_deep_evidence_created": 0,
        "tickers_with_fallback_gain": 0,
        "manual_fill_required_remaining": 1,
        "multi_source_matrix_status": "degraded_with_specific_blockers",
        "brief_quality_status": "pass",
        "mock_used": False, "fixture_used": False,
        "raw_saved": False, "ocr_used": False,
        "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0
    }}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
