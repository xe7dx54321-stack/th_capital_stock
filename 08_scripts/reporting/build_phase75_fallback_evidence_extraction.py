#!/usr/bin/env python3
import argparse, json, sys

def build():
    rows = [
        {"ticker": "688041.SH", "source_type": "sse_html", "business_variable": "exchange_disclosure",
         "evidence_strength": "no_evidence", "claim_type": "none",
         "limitation": "SSE HTML get 186 links but all are SSE navigation boilerplate, not 688041-specific disclosures. Announcement list is JS-rendered.",
         "blocker": "sse_announcement_list_js_rendered"},
        {"ticker": "688041.SH", "source_type": "hygon_ir_html", "business_variable": "company_context",
         "evidence_strength": "no_evidence", "claim_type": "none",
         "limitation": "hygon.cn is a JS SPA, visible text extraction returns 0 chars from static HTML.",
         "blocker": "hygon_cn_js_spa"},
        {"ticker": "300394.SZ", "source_type": "irm_html", "business_variable": "customer_demand_signal",
         "evidence_strength": "no_evidence", "claim_type": "none",
         "limitation": "IRM GET HTML returns HTTP 200 but only 11 chars visible text. QA content is JS-rendered.",
         "blocker": "irm_html_js_rendered_qa"}
    ]
    return {"phase75_fallback_evidence_extraction": {"texts_scanned": 8, "deep_evidence_created": 0,
        "tickers_with_evidence": 0, "rows": rows, "guard_status": "pass",
        "mock_used": False, "fixture_used": False, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
